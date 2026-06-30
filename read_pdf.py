import PyPDF2
with open(r'C:\Users\Nicolas\.gemini\antigravity\scratch\evaluacion2\Evaluacion 4.pdf', 'rb') as f:
    reader = PyPDF2.PdfReader(f)
    text = '\n'.join(page.extract_text() for page in reader.pages)
    print(text)
