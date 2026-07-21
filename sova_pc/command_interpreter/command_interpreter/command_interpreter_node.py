import requests

import rclpy
from rclpy.node import Node
from std_msgs.msg import String

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

# publisher node that publishes the target name to the /search_targets topic

class CommandInterpreterNode(Node):
    def __init__(self):
        super().__init__('command_interpreter_node')
        self.publisher_ = self.create_publisher(String, 'search_targets', 10)
        self.class_names = load_class_names('class_names.txt')
        self.get_logger().info(f"Loaded class names: {self.class_names}")

    def run_once(self):
        user_command = get_user_command()
        target = ask_llm_for_target(user_command, self.class_names)
        self.get_logger().info(f"LLM identified target: {target}")

        msg = String()
        msg.data = target
        self.publisher_.publish(msg)
        self.get_logger().info(f"Published to /search_targets: {target}")



def main(args=None):

    rclpy.init(args=args)
    node = CommandInterpreterNode()
    node.run_once()
    node.destroy_node()
    rclpy.shutdown()




if __name__ == '__main__':
    main()