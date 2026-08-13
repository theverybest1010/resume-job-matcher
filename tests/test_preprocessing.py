from resume_matcher.preprocessing import tokenize


def test_tokenize_tester():
    text = "Python, C++ C# .NET and Node.js"
    result = tokenize(text)

    assert result == ["python", "c++", "c#", ".net", "and", "node.js"]