import api from "./api";

export interface LoginRequest { username: string; password: string; }
export interface AuthResponse { access_token: string; token_type: string; }

const TOKEN_KEY = "copper_token";

export const authService = {
  async login(data: LoginRequest): Promise<AuthResponse> {
    const res = await api.post("/auth/login", data);
    localStorage.setItem(TOKEN_KEY, res.data.access_token);
    api.defaults.headers.common["Authorization"] = `Bearer ${res.data.access_token}`;
    return res.data;
  },

  logout() {
    localStorage.removeItem(TOKEN_KEY);
    delete api.defaults.headers.common["Authorization"];
  },

  getToken(): string | null {
    return localStorage.getItem(TOKEN_KEY);
  },

  isAuthenticated(): boolean {
    return !!this.getToken();
  },

  init() {
    const token = this.getToken();
    if (token) {
      api.defaults.headers.common["Authorization"] = `Bearer ${token}`;
    }
  },
};

authService.init();
export default authService;
