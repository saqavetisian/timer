import os
import random
import subprocess
import tempfile
from datetime import datetime

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

def read_number():
    with open("number.txt", "r") as f:
        return int(f.read().strip())

def write_number(num):
    with open("number.txt", "w") as f:
        f.write(str(num))

def generate_random_commit_message():
    from transformers import pipeline

    generator = pipeline(
        "text-generation",
        model="openai-community/gpt2",
    )
    prompt = """
        Generate a Git commit message following the Conventional Commits standard. The message should include a type, an optional scope, and a subject. Please keep it short. Here are some examples:

        - feat(auth): add user authentication module
        - fix(api): resolve null pointer exception in user endpoint
        - docs(readme): update installation instructions
        - chore(deps): upgrade lodash to version 4.17.21
        - refactor(utils): simplify date formatting logic

        Now, generate a new commit message:
    """
    generated = generator(
        prompt,
        max_new_tokens=50,
        num_return_sequences=1,
        temperature=0.9,  # Slightly higher for creativity
        top_k=50,  # Limits sampling to top 50 logits
        top_p=0.9,  # Nucleus sampling for diversity
        truncation=True,
    )
    text = generated[0]["generated_text"]

    if "- " in text:
        return text.rsplit("- ", 1)[-1].strip()
    else:
        raise ValueError(f"Unexpected generated text {text}")

def git_commit():
    subprocess.run(["git", "add", "number.txt"])
    if "FANCY_JOB_USE_LLM" in os.environ:
        commit_message = generate_random_commit_message()
    else:
        date = datetime.now().strftime("%Y-%m-%d")
        commit_message = f"Update number: {date}"
    subprocess.run(["git", "commit", "-m", commit_message])

def git_push():
    result = subprocess.run(["git", "push"], capture_output=True, text=True)
    if result.returncode == 0:
        print("Changes pushed to GitHub successfully.")
    else:
        print("Error pushing to GitHub:")
        print(result.stderr)

def update_cron_with_random_time():
    random_hour = random.randint(0, 23)
    random_minute = random.randint(0, 59)

    new_cron_command = f"{random_minute} {random_hour} * * * cd {script_dir} && python3 {os.path.join(script_dir, 'update_number.py')}\n"

    if os.name == 'nt':  # Windows
        task_name = "UpdateNumberTask"
        scheduled_time = f"{random_hour:02}:{random_minute:02}"
        subprocess.run([
            "schtasks", "/create", "/tn", task_name, "/tr", f"python {os.path.join(script_dir, 'update_number.py')}",
            "/sc", "daily", "/st", scheduled_time, "/f"
        ])
        print(f"Windows Task Scheduler: Task scheduled for {scheduled_time} daily.")
    else:  # Linux/Mac
        with tempfile.NamedTemporaryFile(delete=False) as temp_cron_file:
            cron_file = temp_cron_file.name

            os.system(f"crontab -l > {cron_file} 2>/dev/null || exit 0")

            with open(cron_file, "r") as file:
                lines = file.readlines()

            with open(cron_file, "w") as file:
                for line in lines:
                    if "update_number.py" not in line:
                        file.write(line)
                file.write(new_cron_command)

            os.system(f"crontab {cron_file}")
            os.remove(cron_file)

        print(f"Cron job updated to run at {random_hour}:{random_minute} tomorrow.")

def main():
    try:
        current_number = read_number()
        new_number = current_number + 1
        write_number(new_number)
        git_commit()
        git_push()
        update_cron_with_random_time()
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(1)

if __name__ == "__main__":
    main()
