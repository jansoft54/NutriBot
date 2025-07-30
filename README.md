# Meal Planner Bot

This is a meal planning assistant with generative AI and data APIs.

## Prerequisites

Before you start, make sure you have the following installed on your system:

- Python 3.10 or newer
- [**uv**](https://github.com/astral-sh/uv): A fast Python package installer and resolver.

## Installation

Follow these steps to get the project up and running.

### 1. Clone the Repository

First, clone the project repository to your local machine.

```bash
git clone https://github.com/your-username/meal-planner-bot.git
cd meal-planner-bot
```

### 2. Set Up Environment Variables

Create a file named `.env` in the root of the project directory. This file will store your secret API keys. Copy the following lines into it:

```env
GEMINI_API_KEY=
SPOONACULAR_API_KEY=
IMAGE_API_KEY=
```

**Important:** Replace the placeholder values with your actual API keys.

### 3. Create Virtual Environment and Install Dependencies

Use `uv` to create a virtual environment and install all the required packages from your `uv.lock` or `pyproject.toml` file.

```bash
# Create a virtual environment named .venv
uv venv

# Activate the virtual environment
# On macOS and Linux:
source .venv/bin/activate
# On Windows (Command Prompt):
.venv\Scripts\activate

# Install all dependencies with uv
uv sync
```

## Running the Application

With the dependencies installed and the environment configured, you can start the web server using `uvicorn`.

```bash
uv run python -m src.main
```
