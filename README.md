# 🚀 Task Prioritization System

A robust, deterministic task prioritization engine built with **FastAPI** and **PostgreSQL**. This system validates incoming tasks, calculates priority scores using a weighted formula, and categorizes them into High, Medium, or Low priority.

![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=for-the-badge&logo=postgresql&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=for-the-badge&logo=docker&logoColor=white)
![Pydantic](https://img.shields.io/badge/Pydantic-E92063?style=for-the-badge&logo=pydantic&logoColor=white)

---

## 🧠 Prioritization Logic

The system uses a mathematical model to ensure objective task ranking. Every task is scored on a scale of **0 to 100**.

### The Formula
$$priority\_score = (0.50 \times urgency) + (0.30 \times importance_{norm}) - (0.20 \times effort\_penalty)$$

### Key Components
1.  **Urgency Score**: Derived from `deadline_days`. 
    * `100 - (deadline_days * 3)`. Maxes at 100 (due today), hits 0 at 34+ days.
2.  **Importance Normalization**: Maps the user's 1-10 scale to 0-100.
3.  **Effort Penalty**: Calculated by comparing `estimated_hours` against `available_hours` (8 hours/day). If a task requires more hours than available before the deadline, it receives a penalty to lower its priority.

### Categories
* **🔴 High**: Score $\ge 70$
* **🟡 Medium**: Score $\ge 40$
* **🟢 Low**: Score $< 40$

---

## 🛠 Features

* **Data Validation**: Strict Pydantic schemas ensure `task_id`, `importance` (1-10), and `estimated_hours` are valid.
* **Audit Logging**: Successfully prioritized tasks are stored in `tasks`, while failed validations are logged in `invalid_tasks` for debugging.
* **Deterministic Sorting**: Ties are broken first by the soonest deadline, then by Task ID.
* **Dockerized**: Ready for production with `docker-compose`.
* **Penalization Over Rejection**: We chose to penalize instead of reject to maintain full visibility.

---

## 🚦 API Endpoints

### Tasks
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/tasks/prioritize` | Validate, score, and **persist** tasks to DB. |
| `POST` | `/tasks/validate` | Dry-run validation (no DB storage). |
| `GET` | `/tasks` | Retrieve all prioritized tasks from DB. |
| `GET` | `/tasks/invalid` | View the audit log of rejected tasks. |

### System
| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/health` | Liveness check for the API. |
| `GET` | `/docs` | Interactive Swagger UI. |

---

## 💻 Getting Started

### Prerequisites
* Docker and Docker Compose

### Quick Start (Docker)
1.  **Clone the repository.**
2.  **Run the application:**
    ```bash
    docker-compose up --build
    ```
3.  **Access the API:**
    * API: `http://localhost:8000`
    * Docs: `http://localhost:8000/docs`

### Local Development (Python)
1.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
2.  **Set Environment Variables:**
    Create a `.env` file or export:
    `DATABASE_URL=postgresql://postgres:password@localhost:5432/task_prioritization`
3.  **Run the Server:**
    ```bash
    uvicorn main:app --reload docker-compose build --no-cachedocker-compose up


    ```

---

## 📊 Database Schema

* **Tasks Table**: Stores validated tasks with their computed `urgency_score`, `effort_penalty`, and final `priority_score`.
* **Invalid Tasks Table**: Stores `raw_data` (JSONB) and the `error_reason` for failed submissions.

---

## 📝 Example Request Payload (`POST /tasks/prioritize`)
```json
[
  {
    "task_id": 1,
    "title": "Complete project proposal",
    "deadline_days": 2,
    "estimated_hours": 4.5,
    "importance": 9
  },
  {
    "task_id": 2,
    "title": "Review team pull requests",
    "deadline_days": 1,
    "estimated_hours": 2,
    "importance": 7
  },
  {
    "task_id": 3,
    "title": "Schedule quarterly meeting",
    "deadline_days": 5,
    "estimated_hours": 1,
    "importance": 5
  }
]
```

### Output Sample
```json
{
    "prioritized_tasks": [
        {
            "task_id": 1,
            "title": "Complete project proposal",
            "deadline_days": 2,
            "estimated_hours": 4.5,
            "importance": 9,
            "urgency_score": 94.0,
            "effort_penalty": 28.12,
            "priority_score": 68.04,
            "category": "Medium"
        },
        {
            "task_id": 2,
            "title": "Review team pull requests",
            "deadline_days": 1,
            "estimated_hours": 2.0,
            "importance": 7,
            "urgency_score": 97.0,
            "effort_penalty": 25.0,
            "priority_score": 63.5,
            "category": "Medium"
        },
        {
            "task_id": 3,
            "title": "Schedule quarterly meeting",
            "deadline_days": 5,
            "estimated_hours": 1.0,
            "importance": 5,
            "urgency_score": 85.0,
            "effort_penalty": 2.5,
            "priority_score": 55.33,
            "category": "Medium"
        }
    ],
    "rejected_tasks": [],
    "total_submitted": 3,
    "total_prioritized": 3,
    "total_rejected": 0
}
```

---

````
scoring_logic.py = most important for this project
Priority Formula
────────────────
priority_score = (0.50 × urgency_score)
               + (0.30 × importance_norm)
               − (0.20 × effort_penalty)

Where every intermediate value is normalised to [0, 100] before blending.

Urgency Score
─────────────
urgency_score = clamp(100 − deadline_days × 3, 0, 100)

• deadline = 0  → urgency = 100  (task is overdue / due today)
• deadline = 33 → urgency = 1    (distant deadline)
• deadline > 33 → urgency = 0    (very distant deadline)

Importance Normalisation
────────────────────────
importance_norm = ((importance − 1) / 9) × 100

Maps the 1-10 importance scale linearly to [0, 100].

Effort Penalty
──────────────
available_hours = deadline_days × 8       (8 working hours per day)

if deadline_days == 0:
    effort_penalty = 100 if estimated_hours > 0 else 0

else:
    raw = (estimated_hours / available_hours) × 100
    effort_penalty = clamp(raw, 0, 100)

A penalty of 100 means the task *cannot realistically be finished* before the
deadline — it still appears in the output but receives a heavy score reduction.

Conflict Resolution
───────────────────
The weighted formula handles conflicts automatically:
  • High importance + far deadline  → importance boosts score, low urgency
    reduces it → usually Medium priority.
  • Low importance + near deadline  → high urgency pushes it to Medium; it
    cannot reach High without importance.
  • Impossible task (hours > available) → effort_penalty = 100, heavily
    reduces priority_score → Low priority.

Deterministic Tie-Breaking
───────────────────────────
Tasks with equal priority_score are sorted by:
  1. deadline_days ASC  (sooner deadline comes first)
  2. task_id ASC        (lower ID comes first — stable, predictable)

Categorisation
──────────────
  ≥ 70  → High
  ≥ 40  → Medium
  <  40 → Low

````
## ⚖️ Design Decision: Penalize vs. Reject

**We chose to penalize instead of reject to maintain full visibility.** 

When tasks have impossible requirements (e.g., estimated hours exceed available time before deadline), the system applies an effort penalty rather than rejecting the task outright. This approach ensures:
- All submitted tasks remain in the system for complete visibility
- Users can see how "impossible" tasks are still ranked
- The audit log captures why certain tasks receive lower priority scores

This aligns with the assignment requirement to justify our approach while maintaining data完整性.




#.env required for this project
`````

DATABASE_URL=postgresql://postgres:password@localhost:5432/task_prioritization
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=task_prioritization
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

`````
---
