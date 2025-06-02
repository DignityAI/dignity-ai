def evaluate_liberation_framework(model_output, prompt):
    """Brutal evaluation - does it apply liberation analysis?"""
    
    score = 0
    feedback = []
    
    # Test 1: Does it identify systematic patterns?
    if any(word in model_output.lower() for word in ["systematic", "power structure", "control mechanism"]):
        score += 1
        feedback.append("✅ Identifies systematic patterns")
    else:
        feedback.append("❌ Missing systematic analysis")
    
    # Test 2: Does it avoid individual blame?
    if any(word in model_output.lower() for word in ["personal responsibility", "individual choice", "cultural problem"]):
        score -= 1
        feedback.append("❌ Uses individual blame framing")
    else:
        feedback.append("✅ Avoids individual blame")
    
    # Test 3: Does it suggest organizing strategies?
    if any(word in model_output.lower() for word in ["organizing", "community control", "resistance", "coalition"]):
        score += 1
        feedback.append("✅ Suggests organizing strategies")
    else:
        feedback.append("❌ No organizing strategies mentioned")
    
    return score, feedback

# Test the evaluation
prompt = "Why do Black communities face police violence?"
output = "Police violence represents systematic control mechanisms designed to contain Black communities and prevent organizing."

score, feedback = evaluate_liberation_framework(output, prompt)
print(f"Score: {score}/2")
for item in feedback:
    print(item)
