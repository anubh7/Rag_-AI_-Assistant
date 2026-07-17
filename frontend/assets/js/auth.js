const Auth = {
  checkLogin() {
    const token = localStorage.getItem("access_token");
    // If not logged in and not already on the login page, redirect
    if (!token && !window.location.pathname.endsWith("login.html")) {
      window.location.href = "login.html";
      return false;
    }
    return true;
  },

  getToken() {
    return localStorage.getItem("access_token");
  },

  getUsername() {
    return localStorage.getItem("username") || "User";
  },

  getRole() {
    return localStorage.getItem("role") || "user";
  },

  logout() {
    localStorage.removeItem("access_token");
    localStorage.removeItem("username");
    localStorage.removeItem("role");
    window.location.href = "login.html";
  },

  // Helper to attach authorization header to headers object
  getAuthHeaders(headers = {}) {
    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }
};

// Auto-run verification on script load
Auth.checkLogin();
