import requests


# turns class_names into a list and ask user to enter command

def load_class_names(filepath):
    with open(filepath, 'r') as f:
        names = [line.strip() for line in f if line.strip()]
    return names


def get_user_command():
    command = input("What should SOVA look for? ")
    return command


# communication wiht llama returning the target' names

def ask_llm_for_target(user_command, class_names):
    prompt = f"""You are SOVA's reasoning system.
The user request is: "{user_command}"
Here is a list of objects that can be detected: {', '.join(class_names)}
Which single object from that list is most relevant to the user's request?
Reply with only the exact object name from the list, nothing else."""

    response = requests.post(
        'http://localhost:11434/api/generate',
        json={
            'model': 'llama3.2',
            'prompt': prompt,
            'stream': False
        }
    )

    result = response.json()
    target_name = result['response'].strip().lower()
    return target_name 


def main():
    class_names = load_class_names('class_names.txt')
    print("Loaded class names:", class_names)

    user_command = get_user_command()
    print("You typed:", user_command)

    target = ask_llm_for_target(user_command, class_names)
    print("LLM identified target:", target)

if __name__ == '__main__':
    main()