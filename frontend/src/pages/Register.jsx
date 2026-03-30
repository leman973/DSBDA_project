import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";

const API_BASE = "http://localhost:8000/api";

export default function Register() {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");

    // Validate passwords match
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // Validate password length
    if (password.length < 6) {
      setError("Password must be at least 6 characters long");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch(`${API_BASE}/auth/register`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username,
          email,
          password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Registration failed");
      }

      // Registration successful, redirect to login
      navigate("/login", { 
        state: { message: "Registration successful! Please log in." } 
      });
    } catch (err) {
      console.error("Registration error:", err);
      setError(err.message || "Failed to register. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "linear-gradient(135deg, hsl(270, 30%, 98%), hsl(280, 40%, 96%))",
      padding: "20px",
    }}>
      <div style={{
        width: "100%",
        maxWidth: "420px",
        background: "white",
        borderRadius: "20px",
        padding: "40px 32px",
        boxShadow: "0 8px 32px hsla(270, 20%, 50%, 0.1)",
        border: "1px solid hsl(270, 20%, 90%)",
      }}>
        {/* Logo/Title */}
        <div style={{ textAlign: "center", marginBottom: "32px" }}>
          <div style={{
            width: 64,
            height: 64,
            margin: "0 auto 16px",
            borderRadius: "50%",
            background: "linear-gradient(135deg, hsl(280, 80%, 60%), hsl(320, 80%, 60%))",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 4px 16px hsla(280, 80%, 60%, 0.3)",
          }}>
            <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
              <path d="M13 2L4.5 13.5H11L10 22L19.5 10.5H13L13 2Z" />
            </svg>
          </div>
          <h1 style={{
            fontSize: "28px",
            fontWeight: 700,
            background: "linear-gradient(135deg, hsl(280, 80%, 60%), hsl(320, 80%, 60%))",
            WebkitBackgroundClip: "text",
            WebkitTextFillColor: "transparent",
            backgroundClip: "text",
            marginBottom: "8px",
          }}>
            Create Account
          </h1>
          <p style={{ color: "hsl(270, 20%, 50%)", fontSize: "15px" }}>
            Sign up to get started with data analysis
          </p>
        </div>

        {/* Error Message */}
        {error && (
          <div style={{
            padding: "12px 16px",
            borderRadius: "12px",
            background: "hsl(0, 70%, 95%)",
            color: "hsl(0, 70%, 40%)",
            fontSize: "14px",
            marginBottom: "20px",
            border: "1px solid hsl(0, 70%, 85%)",
          }}>
            {error}
          </div>
        )}

        {/* Registration Form */}
        <form onSubmit={handleSubmit}>
          {/* Username Field */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{
              display: "block",
              fontSize: "14px",
              fontWeight: 600,
              color: "hsl(270, 30%, 30%)",
              marginBottom: "8px",
            }}>
              Username
            </label>
            <input
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              disabled={isLoading}
              placeholder="Choose a username"
              required
              minLength={3}
              pattern="[a-zA-Z0-9]+"
              title="Username must be alphanumeric"
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: "12px",
                border: "1px solid hsl(270, 20%, 85%)",
                fontSize: "15px",
                fontFamily: "'Space Grotesk', sans-serif",
                outline: "none",
                transition: "border-color 0.2s",
                boxSizing: "border-box",
              }}
              onFocus={(e) => e.target.style.borderColor = "hsl(280, 80%, 60%)"}
              onBlur={(e) => e.target.style.borderColor = "hsl(270, 20%, 85%)"}
            />
          </div>

          {/* Email Field */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{
              display: "block",
              fontSize: "14px",
              fontWeight: 600,
              color: "hsl(270, 30%, 30%)",
              marginBottom: "8px",
            }}>
              Email
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={isLoading}
              placeholder="Enter your email"
              required
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: "12px",
                border: "1px solid hsl(270, 20%, 85%)",
                fontSize: "15px",
                fontFamily: "'Space Grotesk', sans-serif",
                outline: "none",
                transition: "border-color 0.2s",
                boxSizing: "border-box",
              }}
              onFocus={(e) => e.target.style.borderColor = "hsl(280, 80%, 60%)"}
              onBlur={(e) => e.target.style.borderColor = "hsl(270, 20%, 85%)"}
            />
          </div>

          {/* Password Field */}
          <div style={{ marginBottom: "20px" }}>
            <label style={{
              display: "block",
              fontSize: "14px",
              fontWeight: 600,
              color: "hsl(270, 30%, 30%)",
              marginBottom: "8px",
            }}>
              Password
            </label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={isLoading}
              placeholder="Create a password"
              required
              minLength={6}
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: "12px",
                border: "1px solid hsl(270, 20%, 85%)",
                fontSize: "15px",
                fontFamily: "'Space Grotesk', sans-serif",
                outline: "none",
                transition: "border-color 0.2s",
                boxSizing: "border-box",
              }}
              onFocus={(e) => e.target.style.borderColor = "hsl(280, 80%, 60%)"}
              onBlur={(e) => e.target.style.borderColor = "hsl(270, 20%, 85%)"}
            />
          </div>

          {/* Confirm Password Field */}
          <div style={{ marginBottom: "24px" }}>
            <label style={{
              display: "block",
              fontSize: "14px",
              fontWeight: 600,
              color: "hsl(270, 30%, 30%)",
              marginBottom: "8px",
            }}>
              Confirm Password
            </label>
            <input
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              disabled={isLoading}
              placeholder="Confirm your password"
              required
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: "12px",
                border: "1px solid hsl(270, 20%, 85%)",
                fontSize: "15px",
                fontFamily: "'Space Grotesk', sans-serif",
                outline: "none",
                transition: "border-color 0.2s",
                boxSizing: "border-box",
              }}
              onFocus={(e) => e.target.style.borderColor = "hsl(280, 80%, 60%)"}
              onBlur={(e) => e.target.style.borderColor = "hsl(270, 20%, 85%)"}
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: "100%",
              padding: "14px",
              borderRadius: "12px",
              border: "none",
              cursor: isLoading ? "not-allowed" : "pointer",
              background: isLoading 
                ? "hsl(270, 20%, 85%)" 
                : "linear-gradient(135deg, hsl(280, 80%, 60%), hsl(320, 80%, 60%))",
              color: "white",
              fontSize: "16px",
              fontWeight: 600,
              fontFamily: "'Space Grotesk', sans-serif",
              boxShadow: isLoading ? "none" : "0 4px 16px hsla(280, 80%, 60%, 0.3)",
              transition: "all 0.2s",
              opacity: isLoading ? 0.7 : 1,
            }}
            onMouseOver={(e) => { 
              if (!isLoading) {
                e.currentTarget.style.transform = "translateY(-1px)"; 
                e.currentTarget.style.boxShadow = "0 6px 20px hsla(280, 80%, 60%, 0.4)"; 
              }
            }}
            onMouseOut={(e) => { 
              if (!isLoading) {
                e.currentTarget.style.transform = ""; 
                e.currentTarget.style.boxShadow = "0 4px 16px hsla(280, 80%, 60%, 0.3)"; 
              }
            }}
          >
            {isLoading ? "Creating account..." : "Create Account"}
          </button>
        </form>

        {/* Login Link */}
        <div style={{
          marginTop: "24px",
          textAlign: "center",
          fontSize: "14px",
          color: "hsl(270, 20%, 50%)",
        }}>
          Already have an account?{" "}
          <Link 
            to="/login"
            style={{
              color: "hsl(280, 80%, 60%)",
              fontWeight: 600,
              textDecoration: "none",
            }}
            onMouseOver={(e) => e.target.style.textDecoration = "underline"}
            onMouseOut={(e) => e.target.style.textDecoration = "none"}
          >
            Sign in
          </Link>
        </div>
      </div>

      <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
        * { box-sizing: border-box; margin: 0; padding: 0; }
      `}</style>
    </div>
  );
}
