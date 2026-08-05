from pathlib import Path

file_path = Path("src/ml/training/error_classifier.py")
content = file_path.read_text()

# Find the predict method and replace the probability extraction
old_block = '''        proba = self.pipeline.predict_proba([log_text])
        predictions = []
        confidence_scores = {}
        for i, category in enumerate(self.ERROR_CATEGORIES):
            prob = proba[i][0][1] if hasattr(proba[i], 'shape') and proba[i].shape[1] > 1 else proba[i][0]
            confidence_scores[category] = round(float(prob), 3)
            if prob > 0.5:
                predictions.append(category)'''

new_block = '''        proba = self.pipeline.predict_proba([log_text])
        predictions = []
        confidence_scores = {}
        for i, category in enumerate(self.ERROR_CATEGORIES):
            try:
                # OneVsRest returns list of (n_samples, 2) arrays
                cat_proba = proba[i]
                if hasattr(cat_proba, 'shape') and len(cat_proba.shape) >= 2 and cat_proba.shape[1] > 1:
                    prob = float(cat_proba[0][1])
                elif hasattr(cat_proba, '__len__') and len(cat_proba) > 0:
                    prob = float(cat_proba[0]) if len(cat_proba) == 1 else float(cat_proba[1])
                else:
                    prob = 0.0
            except Exception:
                prob = 0.0
            confidence_scores[category] = round(prob, 3)
            if prob > 0.5:
                predictions.append(category)'''

if old_block in content:
    content = content.replace(old_block, new_block)
    file_path.write_text(content)
    print("✅ Fixed predict method!")
else:
    print("⚠️ Could not find exact block. Showing predict method...")
    # Just print lines around predict for manual fix
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'def predict(' in line:
            print(f"Found at line {i+1}")
            for j in range(i, min(i+25, len(lines))):
                print(f"{j+1}: {lines[j]}")

print("\nRestart your server after fixing!")