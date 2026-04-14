                 Users
                   │
                   ▼
        ┌──────────────────┐
        │   AI Gateway     │
        │ (Prompt Router)  │
        └──────────────────┘
                   │
 ┌──────────────┬──────────────┬──────────────┐
 ▼              ▼              ▼
Memory      Task Engine    Matching Engine
(User Data) (Generation)   (Recommendations)
 │              │              │
 └──────► PostgreSQL ◄─────────┘
                   │
                   ▼
             Platform Features
