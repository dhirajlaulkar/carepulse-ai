try:
    with open('data/patients.csv', 'r', encoding='utf-8') as f:
        lines = f.readlines()
        print(f"Total lines: {len(lines)}")
        print("Line 1:", lines[0].strip())
        print("Line 2:", lines[1].strip())
        if len(lines) > 3377:
            print("Line 3377:", lines[3376].strip())
            print("Line 3378:", lines[3377].strip())
except Exception as e:
    print(f"Error: {e}")
