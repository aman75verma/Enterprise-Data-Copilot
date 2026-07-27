# Frontend Architecture and React Concepts

This document provides a high-level overview of how the frontend of the Enterprise Data Copilot application is structured, and the React concepts that make it work. 

## 1. Structure

The frontend is built as a **Single Page Application (SPA)** using React and Vite. This means that instead of the server sending a new HTML page for every click, the server sends a single `index.html` file, and React takes over rendering different "pages" using JavaScript on the client side.

### Key Directories
- **`src/pages/`**: Contains the main top-level views of the application (e.g., `Chat.tsx` for the main interface, `AdminDashboard.tsx`, `Login.tsx`).
- **`src/components/`**: Reusable UI blocks that are shared across pages. Examples include:
  - `MessageBubble.tsx`: Renders individual chat messages.
  - `ToolCallTrace.tsx`: Renders the expandable UI showing how the AI executed an MCP tool.
  - `TopNav.tsx`: The navigation bar at the top.
- **`src/api/`**: Contains `client.ts` which is responsible for fetching data from the FastAPI backend. It abstracts away `fetch()` calls so the React components just call clean JavaScript functions (e.g., `api.chat(...)`).
- **`src/assets/`**: Static images and icons.

## 2. React Concepts Used

### Components (`.tsx` files)
React is built on the idea of **Components**. A component is a JavaScript function that returns JSX (which looks like HTML). By breaking the UI into smaller components (like a `MessageBubble`), you can reuse them anywhere without duplicating code.

### State (`useState`)
React components have memory, called **state**. 
When state changes, React automatically re-renders the component to show the updated data on the screen.
For example, in a chat application, the list of messages is stored in state. When a new message arrives from the backend, we add it to the state array, and React instantly updates the screen.

```tsx
const [messages, setMessages] = useState([]);
```

### Effects (`useEffect`)
The `useEffect` hook allows a component to perform side effects, such as fetching data from a server when the page first loads, or subscribing to events.
For example, in the `AdminDashboard`, a `useEffect` hook triggers the moment the page opens to fetch the latest tool execution logs from the backend.

### React Router
We use `react-router-dom` for **routing**. 
Routing is how the application knows which component to show based on the URL. 
- If the URL is `/`, it renders the `Chat` page.
- If the URL is `/admin`, it renders the `AdminDashboard`.
Because this is a Single Page Application, clicking a link doesn't cause a full page refresh. Instead, React Router intercepts the click, updates the URL, and instantly swaps out the rendered components.

### Props (Properties)
Props are how components talk to each other. A parent component can pass data (or even functions) down to its child components. 
For example, the `Chat` component passes individual message data down to the `MessageBubble` component via props.

## 3. Styling
The application uses modern Vanilla CSS (`src/index.css` and `src/App.css`) paired with **CSS Variables (Custom Properties)**. This approach keeps styles very clean and makes it extremely easy to support things like Dark Mode by simply swapping the variable definitions at the root level.
