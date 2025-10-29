/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          DEFAULT: "#2B7A78",
          light: "#3AAFA9",
          dark: "#17252A",
        },
      },
    },
  },
  plugins: [],
};
