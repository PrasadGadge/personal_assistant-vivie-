class SelfReflection:

    def evaluate(self, question, answer):

        if len(answer) < 50:
            return answer

        improved = answer

        if "I don't know" in answer.lower():
            improved = "Let me analyze that more carefully. " + answer

        return improved