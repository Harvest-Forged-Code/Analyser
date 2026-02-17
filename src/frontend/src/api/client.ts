import axios from "axios";

const apiClient = axios.create({
  baseURL: "http://localhost:8741/api",
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

export default apiClient;
