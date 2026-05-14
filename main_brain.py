# ==================================================
# main_brain.py
# Fixed: TOCTOU race on processing_lock,
#        duplicate update_ui, send_whatsapp return,
#        silent loop exceptions, set_speaking missing,
#        sig_memory_update dropping second arg
# ==================================================

try:
    from Vivie_UI import get_ui
    UI_AVAILABLE = True
except Exception:
    UI_AVAILABLE = False

from Automation.Automation_brain import Auto_main_brain, REDIRECT_PREFIX
from SpeechToText.vivie_stt import listen
from TextToSpeech.Fast_DF_TTS import speak, speak_blocking, stop_speaking
from TextToSpeech.Fast_DF_TTS import is_speaking as tts_is_speaking
from Vivie_UI import start_websocket_server, emit_to_ui

from queue import Queue
input_queue  = Queue()
output_queue = Queue()

import threading
import time
import os
import re

from Core_structure.tool_manifest import (
    discover_tools, inject_into_intent_engine,
    inject_into_planner, inject_into_tool_router,
    execute_tool, get_tool
)
from Core_structure.behavior_engine import (
    record_behavior, get_suggestions,
    get_pattern_summary, start_behavior_engine
)
from Core_structure.personality_engine import (
    detect_signals, evolve_personality, get_personality_status
)
from Core_structure.digital_life_controller import (
    get_dlc, start_digital_life_controller, get_dlc_log
)
from Core_structure.self_awareness_engine import (
    get_capability_status, describe_current_state,
    assess_confidence, get_growth_summary,
    self_reflect, record_growth_event
)
from Features.web_search import search_web
from memory_core.memory_service import retrieve_memory, store_memory
from Time_operations.time_managar import input_manage, input_manage_Alam
from memory_core.episodic_memory import update_last_reaction
from Features.check_internet_speed import get_internet_speed
from Brain.cl_brain import Main_Brain, Main_Brain_Stream
from Features.create_file import create_file
from Features.weather_system import start_weather_system, speak_weather, speak_forecast
from Features.morning_brief import morning_brief
from Vision.Vibrain import capture_image_and_save, vision_brain
from Features.whatsapp_bot import send_msg
from Features.image_generator import GenerateImages
from Core_structure.response_formatter import format_response
from Core_structure.proactive_engine import start_proactive_engine, add_reminder
from Core_structure.research_engine import get_research_engine
from knowledge_core.rag_retrieve import retrieve_knowledge
from knowledge_core.rag_store import store_knowledge
from knowledge_core.knowledge_extractor import extract_knowledge
from Core_structure.agent_router import route_to_agent
from Core_structure.auto_learning_engine import start_auto_learning
from memory_core.session_memory import get_session_memory

from Core_structure.decision_engine import DecisionEngine
from Core_structure.intent_engine import IntentEngine
from Core_structure.context import ContextManager
from Core_structure.plan import Planner
from Core_structure.tool_router import ToolRouter
from Core_structure.self_reflection import SelfReflection
from Core_structure.reasoning_engine import ReasoningEngine

from voice_state import set_speaking, is_speaking as voice_is_speaking, wait_until_done

# ===============================
# GLOBAL VARIABLES
# ===============================
intent_engine   = IntentEngine()
context_manager = ContextManager()
planner         = Planner()
tool_router     = ToolRouter()
reasoning_engine = ReasoningEngine()
self_reflection  = SelfReflection()
decision_engine  = DecisionEngine()

last_news_results = []
last_processed    = ""

numbers    = ["1:", "2:", "3:", "4:", "5:", "6:", "7:", "8:", "9:"]
spl_number = ["11:", "12:"]

# FIX: single Lock — no race-prone .locked() check anywhere
processing_lock = threading.Lock()

VIVIE_ACTIVE = True

REALTIME_KEYWORDS = [
    "current", "latest", "today", "news",
    "live", "price", "stock", "weather now"
]

# ===============================
# REGISTER TOOLS
# ===============================
tool_router.register("create_file",          create_file)
tool_router.register("check_internet_speed", get_internet_speed)
tool_router.register("send_whatsapp",        send_msg)
tool_router.register("generate_image",       GenerateImages)
tool_router.register("get_weather",          speak_weather)
tool_router.register("get_forecast",         speak_forecast)


# ===============================
# UI UPDATE — single definition
# FIX: removed duplicate PyQt version at top.
#      All UI comms go through WebSocket.
# ===============================
def update_ui(signal_name: str, *args):
    """Route any signal through the WebSocket bridge."""
    try:
        # sig_memory_update needs two values — pack them as a dict
        # FIX: previously only args[0] was forwarded, dropping chroma_count
        if signal_name == "sig_memory_update" and len(args) >= 2:
            emit_to_ui(signal_name, {"episodes": args[0], "knowledge": args[1]})
        else:
            value = args[0] if args else None
            emit_to_ui(signal_name, value)
    except Exception as e:
        print(f"[UI] emit error ({signal_name}): {e}")


# ===============================
# INPUT NORMALIZER
# ===============================
def normalize_input(text):
    text = text.strip().lower()
    text = re.sub(r'\s+', ' ', text)
    return text


# ===============================
# AUTO CORRECTION
# ===============================
def autocorrect_input(text):
    corrections = {
        "network":   "net worth",
        "old he is": "how old is he",
        "whats":     "what is",
        "wht":       "what",
        "recieve":   "receive",
    }
    for wrong, correct in corrections.items():
        if wrong in text:
            text = text.replace(wrong, correct)
    return text


# ===============================
# EMOJI REMOVER
# ===============================
def remove_emojis_for_speech(text):
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002700-\U000027BF"
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE
    )
    return emoji_pattern.sub('', text)


# ===============================
# CONTROLLED SPEAK
# FIX: now calls set_speaking(True/False) so voice_state
#      reflects reality — listen_loop interrupt detection works
# ===============================
def controlled_speak(text: str, intent: str = "chat"):
    """Speak text sequentially. 
    Since this is called by tts_loop (which is already a thread), 
    we speak directly here to ensure messages are played one after another.
    """
    global VIVIE_ACTIVE
    if not VIVIE_ACTIVE:
        return

    # 1. Set state to speaking
    update_ui("sig_agent_state", "Speaking...")
    update_ui("sig_speaking_state", True)
    set_speaking(True)

    try:
        # 2. Clean and split text into sentences
        clean = remove_emojis_for_speech(text)
        sentences = [s.strip() for s in clean.split(". ") if s.strip()]

        # 3. Speak each sentence. 
        # speak_blocking will pause this loop until the sentence is finished.
        for sentence in sentences:
            if not VIVIE_ACTIVE:
                break
            speak_blocking(sentence, intent=intent)
            
    except Exception as e:
        print(f"[TTS Execution Error]: {e}")
    finally:
        # 4. Always reset state to standby when done
        set_speaking(False)
        update_ui("sig_speaking_state", False)
        update_ui("sig_agent_state", "Standby")


# ===============================
# CITY EXTRACTOR
# ===============================
def extract_city(text, keyword):
    if keyword in text:
        after = text.split(keyword, 1)[1].strip()
        if after.startswith("in "):
            return after[3:].strip()
    return None


# ===============================
# PERSONAL FACT DETECTOR
# ===============================
def is_personal_statement(text):
    text = text.lower().strip()
    question_words = ["what","where","when","why","how","who","which","do","does","did","can","could"]
    if any(text.startswith(q) for q in question_words):
        return False
    indicators = [
        "remember that","remember","i am","i'm","i live in",
        "my name is","my favourite is","my favorite is",
        "i like","i love","i work at","i study at","i prefer"
    ]
    return any(word in text for word in indicators)


# ===============================
# NUMBER EXTRACTOR
# ===============================
def extract_number(text):
    match = re.search(r'\d+', text)
    return int(match.group()) - 1 if match else None


# ===============================
# WAKE WORD FIX
# ===============================
def fix_wake_word(text):
    text = text.lower()
    for v in ["vivi","vv","baby","bibi","biwi","vee vee","abp","v8","bbp","pv","vb"]:
        if v in text:
            text = text.replace(v, "vivie")
    return text


# ===============================
# MAIN INPUT PROCESSOR
# ===============================
def process_text(text: str):
    update_ui("sig_agent_state", "processing...")

    if any(x in text.lower() for x in ["[tts]", "vivie :", "speaking:"]):
        print("[BRAIN] TTS marker detected — skipping.")
        return None

    global last_news_results, VIVIE_ACTIVE

    text = normalize_input(text)
    text = autocorrect_input(text)
    text = fix_wake_word(text)

    # ── Kill switch ──────────────────────────────
    stop_words = ["go to sleep","vivie silence","vivie stop","vivie keep quiet",
                  "vivie shut down","stop vivie"]
    if "stop" in text or any(w in text for w in stop_words):
        VIVIE_ACTIVE = False
        return "Okay, going silent Boss."

    wake_words = ["wake up","vivie wake up","vivie start","vivie speak"]
    if text.strip().lower() == "start" or any(w in text for w in wake_words):
        VIVIE_ACTIVE = True
        return "Hey Boss, I am back."

    if not VIVIE_ACTIVE:
        return None

    # ── Reaction detection ───────────────────────
    if any(w in text for w in ["good answer","correct","well done","perfect answer"]):
        update_last_reaction("positive")
        try: evolve_personality({"general_positive": True})
        except Exception: pass
        return "Glad that helped Boss."

    if any(w in text for w in ["wrong answer","incorrect","that was wrong","bad answer","improve more"]):
        update_last_reaction("negative")
        try: evolve_personality({"general_negative": True})
        except Exception: pass
        return "Noted. I will do better."

    # ── Intent + Planning ────────────────────────
    intent  = intent_engine.detect(text, context_manager.__dict__)
    context = {"last_input": text}
    primary_intent = intent.get("primary", "chat")
    confidence = intent.get("confidence", 0)

    print(f"🧠 User: {text}")
    print(f"🎯 Intent: {intent}")
    update_ui("sig_user_message", text)
    update_ui("sig_listening", False)

    record_behavior(action=intent.get("primary", "chat"), context=text[:80])
    actions = planner.generate_plan(intent, context)
    print("🛠 Actions:", actions)

    # Early memory + knowledge retrieval
    memory_block     = ""
    knowledge_context = ""
    try:
        mem_ctx = retrieve_memory(text)
        msgs    = mem_ctx.get() if mem_ctx else []
        memory_block = "".join(m.get("content", "") + "\n" for m in msgs)
    except Exception:
        pass
    try:
        knowledge_context = retrieve_knowledge(text) or ""
    except Exception:
        pass

    # ── Time & Alarm ─────────────────────────────
    if text.startswith("tell me"):
        if any(char.isdigit() for char in text):
            text = text.replace(" p.m.", "PM").replace(" a.m.", "AM")
            for num in spl_number if any(n in text for n in spl_number) else numbers:
                if num in text:
                    text = text.replace(num, f"0{num}")
            input_manage(text)
            return None

    elif text.startswith("set alarm"):
        text = text.replace(" p.m.", "PM").replace(" a.m.", "AM")
        for num in spl_number if any(n in text for n in spl_number) else numbers:
            if num in text:
                text = text.replace(num, f"0{num}")
        input_manage_Alam(text)
        return None
    
    elif primary_intent == "chat" and confidence >= 0.9 and len(text.split()) < 6:
    # Direct call to Brain for instant response
        response = Main_Brain(f"User said: {text}. Respond naturally, warmly, and very briefly.")
        if response:
            response = format_response(response)
            update_ui("sig_vivie_message", response)
            return response

    # ── Execution ────────────────────────────────
    # FIX: removed `if not processing_lock.locked():` — that was a
    # TOCTOU race. Just acquire the lock directly; if another thread
    # holds it we wait, which is the correct and safe behaviour.
    with processing_lock:

        handled = False
        if primary_intent == "automation" and confidence >= 0.75:
            handled = Auto_main_brain(text)
        if handled:
            return "Done"

        details = text   # safe default before loop

        for act in actions:
            act_type = act["type"]
            details  = act["details"]

            # ── Code triggers (checked once, outside action loop originally)
            code_triggers = [
                "write a function","write a python","write code",
                "write a program","implement","create a function"
            ]
            if any(t in text.lower() for t in code_triggers):
                from Core_structure.agent_router import code_agent
                response = code_agent(text)
                if response:
                    response = format_response(response)
                    update_ui("sig_vivie_message", response)
                    return response

            # ── Tool framework ────────────────────
            tool_result = execute_tool(act_type, details)
            if tool_result:
                response = format_response(tool_result)
                response = self_reflection.evaluate(details, response)
                context_manager.update(intent, details, response)
                info = extract_knowledge(details, response, source="tool")
                if info: store_knowledge(info, {"source": "tool", "query": details[:100]})
                store_memory(details, response)
                update_ui("sig_vivie_message", response)
                return response

            # ── Agent router ──────────────────────
            agent_name, agent_response = route_to_agent(details, memory_block, knowledge_context)
            if agent_name != "none" and agent_response:
                agent_response = format_response(agent_response)
                context_manager.update(intent, details, agent_response)
                info = extract_knowledge(details, agent_response, source="agent")
                if info: store_knowledge(info, {"source": f"{agent_name}_agent", "query": details[:100]})
                store_memory(details, agent_response)
                update_ui("sig_vivie_message", agent_response)
                return agent_response

            # ── Specific action handlers ──────────
            if act_type == "create_file":
                filename = details.replace("create","").replace("file","").strip()
                if not filename:
                    return "Boss, what should I name the file?"
                tool_router.execute("create_file", filename)
                response = format_response("Boss, your file has been created successfully.")
                response = self_reflection.evaluate(details, response)
                update_ui("sig_vivie_message", response)
                return response

            elif act_type == "check_internet_speed":
                speed    = get_internet_speed()
                response = format_response(str(speed) if speed is not None else "Unable to determine internet speed")
                response = self_reflection.evaluate(details, response)
                update_ui("sig_vivie_message", response)
                return response

            elif act_type == "vision_analysis":
                if capture_image_and_save("capture_image.jpg"):
                    response = format_response(vision_brain("capture_image.jpg"))
                    response = self_reflection.evaluate(details, response)
                    update_ui("sig_vivie_message", response)
                    return response
                return "Vision capture failed Boss."

            elif act_type == "get_weather":
                tool_router.execute("get_weather", extract_city(details, "weather"))
                return None

            elif act_type == "get_forecast":
                city = extract_city(details, "forecast")
                tool_router.execute("get_forecast", city) if city else tool_router.execute("get_forecast")
                return None

            elif act_type == "send_whatsapp":
                # FIX: success path now returns — was falling through before
                try:
                    tool_router.execute("send_whatsapp", details)
                    response = "Message sent successfully on WhatsApp."
                except Exception:
                    response = "Failed to send WhatsApp message."
                update_ui("sig_vivie_message", response)
                return response

            elif act_type == "morning_brief":
                morning_brief()
                return "Here's your morning brief, Boss."

            elif act_type == "respond_text":
                lower_text = details.lower()

                # Personality query
                if any(w in lower_text for w in [
                    "how have you evolved","your personality","how are you different",
                    "what have you become","describe yourself","your traits"
                ]):
                    status = get_personality_status()
                    record_growth_event("personality_evolved", str(status))
                    update_ui("sig_vivie_message", status)
                    return status

                # News explain
                if any(k in lower_text for k in ["explain number","open number","tell me about number"]):
                    index = extract_number(lower_text)
                    if index is not None and 0 <= index < len(last_news_results):
                        article = last_news_results[index]
                        response = Main_Brain(
                            f"Explain clearly:\ntitle:{article['title']}\n"
                            f"Context:{article['content']}\nsource:{article['source']}"
                        )
                        if response:
                            context_manager.update(intent, details, response)
                            update_ui("sig_vivie_message", response)
                            return response
                    return "Please select a valid headline number."

                # Latest news
                if any(k in lower_text for k in [
                    "latest news","tell latest news","current news",
                    "today news","news today","tell today news"
                ]):
                    news_results = search_web("latest world news today")
                    if news_results:
                        last_news_results = news_results
                        headlines = "Here are the latest headlines:\n\n"
                        for i, article in enumerate(news_results):
                            title = article["title"].split(".")[0]
                            headlines += f"{i+1}.{title}\n"
                        headlines += "\nWhich one would you like me to explain?"
                        update_ui("sig_vivie_message", headlines)
                        return headlines
                    return "I could not fetch the latest news right now."

                # Reminder
                if any(t in lower_text for t in [
                    "remind me to","remind me at","set reminder",
                    "reminder for","don't let me forget"
                ]):
                    response = Main_Brain(
                        f"Extract reminder time and task from: '{details}'\n"
                        f"Reply in format: TIME|TASK\n"
                        f"TIME: HH:MM or YYYY-MM-DD HH:MM\nExample: 14:30|Submit assignment\n"
                        f"Only reply with TIME|TASK."
                    )
                    if response and "|" in response:
                        parts  = response.strip().split("|")
                        r_time = parts[0].strip()
                        r_task = parts[1].strip()
                        add_reminder(r_task, r_time)
                        msg = f"Got it Boss. I'll remind you to {r_task} at {r_time}."
                        update_ui("sig_vivie_message", msg)
                        return msg
                    return "Boss, please tell me the time for the reminder."

                # Pattern query
                if any(w in lower_text for w in [
                    "what do you know about my habits","what have you learned about me",
                    "my patterns","my routine","my habits"
                ]):
                    summary = get_pattern_summary()
                    update_ui("sig_vivie_message", summary)
                    return summary

                # Personal memory
                if is_personal_statement(details):
                    store_memory(details, "")
                    response = "Noted. I will remember that."
                    context_manager.update(intent, details, response)
                    update_ui("sig_vivie_message", response)
                    return response

                # Real-time query
                if any(word in lower_text for word in REALTIME_KEYWORDS):
                    web_data    = search_web(details)
                    final_input = (
                        f"Use real-time web data:\n{web_data}\n\n"
                        f"Summarize clearly.\n\nUser: {details}"
                    )
                    response = Main_Brain(final_input)
                    if response:
                        context_manager.update(intent, details, response)
                        update_ui("sig_vivie_message", response)
                        return response

                # Knowledge map
                if any(w in lower_text for w in [
                    "knowledge map","what have you researched",
                    "research history","show knowledge graph",
                    "what do you know about connections"
                ]):
                    engine = get_research_engine()
                    topic  = None
                    for prep in ["about","for","on"]:
                        if prep in lower_text:
                            topic = lower_text[lower_text.index(prep)+len(prep):].strip()
                            break
                    result = engine.get_knowledge_map(topic)
                    update_ui("sig_vivie_message", result)
                    return result

                # Research history
                if any(w in lower_text for w in [
                    "research history","what have you researched before",
                    "previous research","past research"
                ]):
                    engine = get_research_engine()
                    record_growth_event("learned_topic", f"Researched: {details[:50]}")
                    result = engine.get_research_history()
                    update_ui("sig_vivie_message", result)
                    return result

                # Digital life status
                if any(w in lower_text for w in [
                    "what have you done","autonomous actions","digital life status",
                    "dlc status","what did you do","show activity log"
                ]):
                    result = get_dlc().get_status()
                    update_ui("sig_vivie_message", result)
                    return result[:300]

                # Watch folder
                if any(w in lower_text for w in ["watch folder","monitor folder","add folder"]):
                    response = Main_Brain(f"Extract folder path from: '{details}'\nReturn ONLY the path.")
                    if response and os.path.exists(response.strip()):
                        get_dlc().add_watch_folder(response.strip())
                        msg = f"Now monitoring {response.strip()}"
                        update_ui("sig_vivie_message", msg)
                        return msg

                # Active routines
                if any(w in lower_text for w in ["my routines","show routines","what routines","active routines"]):
                    result = get_dlc().routine_manager.get_routine_status()
                    update_ui("sig_vivie_message", result)
                    return result[:300]

                # Self-awareness
                self_awareness_triggers = {
                    "what can you do":          lambda: get_capability_status(),
                    "your capabilities":        lambda: get_capability_status(),
                    "what are you capable of":  lambda: get_capability_status(),
                    "how are you doing":        lambda: describe_current_state(),
                    "your current state":       lambda: describe_current_state(),
                    "system status":            lambda: describe_current_state(),
                    "your growth":              lambda: get_growth_summary(),
                    "how have you grown":       lambda: get_growth_summary(),
                    "reflect on yourself":      lambda: self_reflect(),
                    "honest reflection":        lambda: self_reflect(),
                    "what are your limits":     lambda: get_capability_status(),
                    "what can't you do":        lambda: get_capability_status(),
                    "your vision capability":   lambda: get_capability_status("vision"),
                    "your research capability": lambda: get_capability_status("research"),
                }
                for trigger, handler in self_awareness_triggers.items():
                    if trigger in lower_text:
                        result = handler()
                        update_ui("sig_vivie_message", result)
                        return result[:400]

                # ── Decision Engine + LLM ─────────
                mem_block2 = memory_block
                knowledge2 = knowledge_context
                if not mem_block2:
                    mem_ctx2   = retrieve_memory(details)
                    msgs2      = mem_ctx2.get() if mem_ctx2 else []
                    mem_block2 = "".join(m.get("content","") + "\n" for m in msgs2)

                if not knowledge2:
                    knowledge2 = retrieve_knowledge(details) or ""
                contextual_input = context_manager.build_context_prompt(details)

                reasoning_steps = reasoning_engine.think(
                    details, intent, mem_block2, knowledge2
                )
                print("\n🧠 Reasoning:")
                for step in reasoning_steps: print(" •", step)
                update_ui("sig_reasoning", reasoning_steps)

                decision = decision_engine.decide(
                    user_input   = details,
                    intent       = intent,
                    memory_block = mem_block2,
                    knowledge    = knowledge2,
                    context      = contextual_input,
                    reasoning    = reasoning_steps
                )
                print(f"⚡ {decision['priority_action']} | {decision['response_depth']} | conf={decision['confidence']}")
                update_ui("sig_confidence", round(decision.get("confidence", 0.8) * 100, 1))

                if decision["use_web_search"]:
                    web_data = search_web(details)
                    if web_data:
                        decision["top_knowledge"] = (decision.get("top_knowledge") or "") + f"\nReal-time:\n{str(web_data)[:1000]}"

                final_input = decision_engine.build_smart_prompt(
                    user_input = details,
                    decision   = decision,
                    context    = contextual_input,
                    reasoning  = reasoning_steps
                )

                try:
                    confidence_data = assess_confidence(details, knowledge_context or "", mem_block2)
                except Exception:
                    confidence_data = {"should_refuse": False, "be_honest": False, "should_search": False, "caveat": ""}

                if confidence_data["should_refuse"]:
                    response = f"Boss, {confidence_data['caveat']}"
                    update_ui("sig_vivie_message", response)
                    return response

                if confidence_data["be_honest"]:
                    final_input = (
                        f"Important: answer with appropriate uncertainty. "
                        f"{confidence_data['caveat']}\n\n"
                    ) + final_input

                if confidence_data["should_search"] and not any(w in lower_text for w in REALTIME_KEYWORDS):
                    web_data = search_web(details)
                    if web_data:
                        final_input = f"Real-time data:\n{web_data}\n\n" + final_input

                try:
                    response = Main_Brain(final_input)
                except Exception as e:
                    # This will print the FULL error, including the line number and the exact API error (e.g., 429 Quota Exceeded)
                    import traceback
                    print("\n" + "="*50)
                    print("🔴 CRITICAL LLM ERROR DETECTED")
                    print(f"Error Type: {type(e).__name__}")
                    print(f"Error Message: {str(e)}")
                    traceback.print_exc() # This tells you EXACTLY which line in which file failed
                    print("="*50 + "\n")
    
                    # Provide a more helpful response based on the error
                    if "429" in str(e):
                        return "Boss, I've hit my API limit (Quota Exceeded). I need a moment to cool down or a new key."
                    elif "timeout" in str(e).lower():
                        return "My connection timed out, Boss. I'll try to reconnect."
                    else:
                        return "I encountered a neural glitch. Check the console for the error log."


                if response:
                    response = format_response(response)
                    response = self_reflection.evaluate(details, response)
                    context_manager.update(intent, details, response)
                    store_memory(details, response)
                    _emit_memory_counts()
                    try:
                        signals = detect_signals(
                            user_input     = details,
                            vivie_response = response,
                            intent         = str(intent.get("primary", "chat")),
                            reaction       = "neutral"
                        )
                        evolve_personality(signals)
                    except Exception:
                        pass
                    update_ui("sig_vivie_message", response)
                    return f"__stream__:{final_input}"  # tag for streaming TTS

        # ── Fallback: no action handled it ───────
        contextual_input = context_manager.build_context_prompt(details)
        response = Main_Brain(contextual_input)
        if response:
            context_manager.update(intent, details, response)
            store_memory(details, response)
            _emit_memory_counts()
            try:
                signals = detect_signals(
                    user_input     = details,
                    vivie_response = response,
                    intent         = str(intent.get("primary", "chat")),
                    reaction       = "neutral"
                )
                evolve_personality(signals)
            except Exception:
                pass
            update_ui("sig_vivie_message", response)
            try:
                from memory_core.episodic_memory import _load_episodes
                from knowledge_core.chroma_manager import get_chroma_manager
                from memory_core.session_memory import get_session_memory
                stats = get_session_memory().get_session_stats()
                # FIX: pass both values — update_ui now forwards both correctly
                update_ui("sig_memory_update",
                          len(_load_episodes()),
                          get_chroma_manager().count())
                update_ui("sig_session_id", f"S{stats.get('total_sessions',1):04d}")
            except Exception:
                pass
            return response


# ===============================
# LISTEN LOOP
# ===============================
def listen_loop():
    while True:
        try:
            update_ui("sig_agent_state", "listening...")
            update_ui("sig_listening", True)
            text = listen()
            update_ui("sig_listening", False)

            if text and text.strip():
                print(f"[QUEUE] Input: {text}")
                if tts_is_speaking():
                    print("⚡ Interrupting Vivie...")
                    stop_speaking()
                input_queue.put(text.strip())

        except Exception as e:
            update_ui("sig_listening", False)
            print(f"[STT Error]: {e}")
            time.sleep(0.2)


# ===============================
# BRAIN LOOP
# FIX: logs exceptions instead of silently swallowing them
# ===============================

def brain_loop():
    global last_processed

    while True:
        try:
            text = input_queue.get(timeout=0.2)
            if isinstance(text, str) and text.startswith(REDIRECT_PREFIX):
                text = text[len(REDIRECT_PREFIX):]
            if text == last_processed:
                continue
            last_processed = text

            response = process_text(text)
            if response:
                from TextToSpeech.voice_personality import detect_voice_mood

                # Streaming responses are tagged — pass prompt directly
                if isinstance(response, str) and response.startswith("__stream__:"):
                    output_queue.put((response, "chat"))
                else:
                    # Pre-built response (tools, agents) — detect mood normally
                    mood = detect_voice_mood(response)
                    output_queue.put((response, mood))

        except Exception as e:
            if str(e):
                print(f"[BrainLoop Error]: {e}")
            continue


# ===============================
# TTS LOOP
# FIX: logs exceptions instead of silently swallowing them
# ===============================

def _speak_stream(prompt: str, intent: str = "chat"):
    """
    Stream LLM response directly to TTS sentence by sentence.
    First sentence spoken in ~0.5s.
    """
    global VIVIE_ACTIVE
    if not VIVIE_ACTIVE:
        return

    update_ui("sig_agent_state", "Speaking...")
    update_ui("sig_speaking_state", True)
    set_speaking(True)

    spoken_sentences = []

    def _on_sentence(sentence: str):
        """Called for each sentence as it streams in."""
        if not VIVIE_ACTIVE:
            return
        clean = remove_emojis_for_speech(sentence)
        if clean.strip():
            spoken_sentences.append(clean)
            speak_blocking(clean, intent=intent)

    try:
        full_response = Main_Brain_Stream(prompt, on_sentence=_on_sentence)

        # Update UI with complete response
        if full_response:
            update_ui("sig_vivie_message", full_response)

    except Exception as e:
        print(f"[Stream Error]: {e}")
    finally:
        set_speaking(False)
        update_ui("sig_speaking_state", False)
        update_ui("sig_agent_state", "Standby")


def tts_loop():
    """
    Streaming TTS loop.
    Pulls (response, intent) from output_queue.
    For streaming responses, speaks each sentence
    as it arrives instead of waiting for full response.
    """
    while True:
        try:
            item = output_queue.get(timeout=0.2)

            if isinstance(item, tuple):
                response, intent = item
            else:
                response, intent = item, "chat"

            if not response:
                continue

            # Check if this is a streaming prompt or a pre-built response
            # Streaming prompts are tagged with "__stream__" prefix
            if isinstance(response, str) and response.startswith("__stream__:"):
                prompt = response[len("__stream__:"):]
                _speak_stream(prompt, intent)
            else:
                # Pre-built response (from tools, agents, etc.) — speak directly
                controlled_speak(response, intent=intent)

        except Exception as e:
            if str(e):
                print(f"[TTS Loop Error]: {e}")
            continue


# ===============================
# BEHAVIOR SUGGESTIONS → UI
# ===============================
def _push_behavior_suggestions_to_ui():
    import datetime
    time.sleep(90)

    while True:
        try:
            suggestions = get_suggestions(top_k=3)
            if suggestions:
                for sug in suggestions:
                    now = datetime.datetime.now().strftime("%H:%M:%S")
                    update_ui("sig_log", f"[{now}] 💡 {sug['message']}")
        except Exception as e:
            print(f"[BehaviorSuggestions] Error: {e}")

        time.sleep(1800)
        
# ===============================
# MEMORY + KNOWLEDGE COUNTS → UI
# =============================== 
def _emit_memory_counts():
    """Push live memory + knowledge counts to UI."""
    try:
        from memory_core.episodic_memory import _load_episodes
        from knowledge_core.chroma_manager import get_chroma_manager
        update_ui("sig_memory_update", {
            "episodes":  len(_load_episodes()),
            "knowledge": get_chroma_manager().count()
        })
    except Exception:
        pass
 
def _push_startup_data():
    """
    Push real data to UI 3s after startup.
    Gives WebSocket time to connect and browser to load.
    """
    import time, threading

    def _worker():
        time.sleep(3)
        try:
            # Session ID
            from memory_core.session_memory import get_session_memory
            session = get_session_memory()
            stats   = session.get_session_stats()
            session_id = f"S{stats.get('total_sessions', 1):04d}"
            update_ui("sig_session_id", session_id)
        except Exception:
            pass

        try:
            # Episode count + knowledge count
            from memory_core.episodic_memory import _load_episodes
            from knowledge_core.chroma_manager import get_chroma_manager
            ep_count     = len(_load_episodes())
            chroma_count = get_chroma_manager().count()
            update_ui("sig_memory_update", ep_count, chroma_count)
            _emit_memory_counts()
        except Exception:
            pass

        try:
            # Confidence from personality engine
            from Core_structure.personality_engine import _load
            p = _load()
            pos   = p.get("positive_reactions", 0)
            neg   = p.get("negative_reactions", 0)
            total = pos + neg
            conf  = round((pos / total * 30) + 70, 1) if total > 0 else 97.0
            update_ui("sig_confidence", conf)
        except Exception:
            pass

        update_ui("sig_log", "System initialized — all engines online")

    threading.Thread(target=_worker, daemon=True).start()

# ===============================
# VIVIE STARTUP
# ===============================
def Vivie():
    print("🌸 Vivie is starting...")
 
    discover_tools()
    inject_into_intent_engine(intent_engine)
    inject_into_planner(planner)
    inject_into_tool_router(tool_router)
    print("🔧 Tool framework ready.")
 
    start_weather_system()
    start_proactive_engine()
    start_auto_learning()
    record_growth_event("learned_topic", "Initial setup complete")
    start_behavior_engine()
    start_digital_life_controller()
    start_websocket_server()
    _push_startup_data()
    
 
    # Push real startup data to UI (after WS starts)
    import time as _t; _t.sleep(1.2)
 
    try:
        stats = get_session_memory().get_session_stats()
        update_ui("sig_session_id", str(stats.get("total_sessions", 1)))
    except Exception:
        pass
 
    _emit_memory_counts()
 
    try:
        greeting = get_session_memory().get_session_greeting()
        if greeting:
            speak_blocking(greeting)
    except Exception as e:
        print(f"[SessionMemory Error]: {e}")
 
    t1 = threading.Thread(target=listen_loop,                      daemon=True)
    t2 = threading.Thread(target=brain_loop,                       daemon=True)
    t3 = threading.Thread(target=tts_loop,                         daemon=True)
    t4 = threading.Thread(target=_push_behavior_suggestions_to_ui, daemon=True)
 
    t1.start(); t2.start(); t3.start(); t4.start()
    t1.join();  t2.join();  t3.join();  t4.join()
