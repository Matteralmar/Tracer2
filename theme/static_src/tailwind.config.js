/**
 * This is a minimal config.
 *
 * If you need the full config, get it from here:
 * https://unpkg.com/browse/tailwindcss@latest/stubs/defaultConfig.stub.js
 */

module.exports = {
    content: [
        // Templates within theme app (e.g. base.html)
            '../templates/**/*.html',
            // Templates in other apps. Uncomment the following line if it matches
            // your project structure or change it to match.
            '../../templates/**/*.html',
            '../../account/templates/**/*.html',
            '../../tickets/templates/**/*.html',
            '../../administration/templates/**/*.html',
            '../../dashboard/templates/**/*.html',
    ],
    theme: {
        extend: {},
    },
    plugins: [
        /**
         * '@tailwindcss/forms' is the forms plugin that provides a minimal styling
         * for forms. If you don't like it or have own styling for forms,
         * comment the line below to disable '@tailwindcss/forms'.
         */
        require('@tailwindcss/forms'),
        require('@tailwindcss/typography'),
        require('@tailwindcss/line-clamp'),
        require('@tailwindcss/aspect-ratio'),
    ],
}
