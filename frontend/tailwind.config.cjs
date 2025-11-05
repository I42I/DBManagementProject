/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: { DEFAULT: "#0ea5e9" },
        accent: { DEFAULT: "#16a34a" }
      }
    },
  },
  plugins: [],
}