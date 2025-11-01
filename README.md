```
online-marketplace/
│
├── frontend/                  
│   ├── public/       
│   ├── src/                   
│   │   ├── assets/            # Images, logos, icons
│   │   ├── components/        # Reusable UI components (Navbar, Footer, ProductCard)
│   │   ├── pages/             # Page-level components (Home, Product, Cart, Profile)
│   │   ├── context/           # React Context API (AuthContext, CartContext)
│   │   ├── hooks/             # Custom hooks (useAuth, useFetch, useCart)
│   │   ├── services/          # API calls (backend & genai)
│   │   ├── styles/            # CSS/SCSS/Tailwind files
│   │   ├── App.jsx
│   │   ├── index.html
│   │   └── main.jsx
│   ├── .gitignore             
│   └── package.json
│
├── backend/                   
│   ├── src/                   
│   │   ├── config/            # Database & environment configs
│   │   ├── controllers/       # Business logic (products, users, orders)
│   │   ├── models/            # Database schemas
│   │   ├── routes/            # Express routes
│   │   ├── middlewares/       # Authentication, error handling
│   │   ├── utils/             # Helper functions
│   │   └── server.js          # App entry point
│   ├── .gitignore             
│   ├── .env                   # Backend environment variables
│   └── package.json
│
├── genai-services/            
│   ├── src/                   
│   │   ├── configs/           # API keys, env setup
│   │   ├── services/          # LLM/Gemini/OpenAI wrappers
│   │   ├── routes/            # Express routes
│   │   ├── controllers/       # Request handling
│   │   ├── utils/             # Pre/post-processing helpers
│   │   └── server.js          # Entry point
│   ├── .gitignore             
│   └── package.json
│
├── docs/                       # Documentation
│
├── .gitignore                  # Root ignore file
└── README.md

```

