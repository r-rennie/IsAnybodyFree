# IsAnybodyFree?
**The fast, automated way to find overlapping office hours.**

**Live Application:** [https://isanybodyfree1.pythonanywhere.com/](https://isanybodyfree1.pythonanywhere.com/)

## 📖 Project Overview
IsAnybodyFree is a professional web application designed to solve the optimization task of scheduling faculty office hours. Instead of manual back-and-forth emails, professors share a unique link where students "drag and select" their availability. The app's core engine then calculates the optimal time slots that provide the highest student coverage.

## 🛠 Features
* **Professor Dashboard:** Manage settings and view recommended office hour windows.
* **Dynamic Matching Engine:** Optimization algorithm that calculates student density per time slot.
* **Unique Slugs:** Secure, shareable URLs for every faculty member (e.g., `/p/dr-fake`).
* **Mobile-Friendly Grid:** Intuitive UI for students to block out class and work schedules.

## 🤖 Agentic Engineering & AI Disclosure
In accordance with the course AI Policy, this application was developed primarily using **Agentic Engineering**.
* **Primary Agent:** Gemini 3 Flash.
* **Tooling Evolution:** Development initially began using the embedded AI agent within VS Code. However, due to severe access and connectivity issues that hindered the workflow, the project was migrated to the Gemini 3 Flash web-based environment. This transition allowed for more stable long-context window management and consistent code generation.
* **AI Citations:**
    * **Architecture:** AI assisted in designing the Application Factory pattern and Flask Blueprint structure to ensure scalability.
    * **Optimization Logic:** The `compute_best_office_hours` algorithm was co-authored with AI to ensure efficient set-coverage logic for student availability.
    * **Refactoring:** AI agents were used to vet generated code for production reliability, identifying edge cases in database transactions.
* **Human Audit:** Every line of AI-generated code was manually reviewed, tested, and modified by the development team to ensure fit-for-purpose reliability and production readiness.


## 🧪 Testing & Reliability
This project features a **robust, comprehensive testing system** using `pytest`.
To run the test suite locally:
1. Ensure your virtual environment is active.
2. Run the command:
   ```bash
   pytest -v
   ```
Tests cover database initialization, route integrity, and the office hour recommendation algorithm.

## 💻 Local Installation (For Humans)
To run this application locally for development or review:

1. **Clone the Repo:**
   ```bash
   git clone https://github.com/r-rennie/IsAnybodyFree.git
   cd IsAnybodyFree
   ```
2. **Setup Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
4. **Run the App:**
   ```bash
   flask run
   ```

## 🤝 Version Control & QA
* **GitHub Hosting:** This project is successfully hosted on GitHub to allow for transparent version control.
* **QA Review:** Active progress was tracked through **Pull Request Days** starting on 4/20. Our group successfully paired with another team to conduct cross-team QA testing and provided constructive criticism on their implementation logic.
