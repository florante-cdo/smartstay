/** Same palette and fonts that base.html used to define for the CDN build. */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./{config,core,campaigns,enquiries,reservations,dashboard}/**/*.py",
    "./static/js/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        garden: { 50: "#f1f6f3", 100: "#dcebe2", 600: "#2f6b4f", 700: "#255640", 900: "#142e22" },
        sand: "#f7f4ee",
      },
      fontFamily: {
        display: ["Fraunces", "Georgia", "serif"],
        body: ['"Source Sans 3"', "system-ui", "sans-serif"],
      },
    },
  },
};
