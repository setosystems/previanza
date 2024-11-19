module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js"
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#ebf3fa',   // Azul muy claro
          100: '#cde0f5',  // Azul claro
          200: '#99bfe9',  // Azul medio claro
          300: '#6699cc',  // Azul medio
          400: '#3377b3',  // Azul más fuerte
          500: '#003F88',  // Azul principal (corporativo)
          600: '#003573',  // Azul oscuro
          700: '#002959',  // Azul muy oscuro
          800: '#001d40',  // Azul profundo
          900: '#001326',  // Azul casi negro
        },
        gray: {
          50: '#f9fafb',   // Blanco-gris claro
          100: '#f4f4f5',  // Gris claro
          200: '#e5e7eb',  // Gris medio claro
          300: '#d1d5db',  // Gris medio
          400: '#9ca3af',  // Gris fuerte
          500: '#6b7280',  // Gris principal
          600: '#4b5563',  // Gris oscuro
          700: '#374151',  // Gris muy oscuro
          800: '#1f2937',  // Gris profundo
          900: '#111827',  // Gris casi negro
        },
        accent: {
          gold: {
            50: '#fcf9f4',   // Dorado muy claro
            100: '#f9f0df',  // Dorado claro
            200: '#f3dfb5',  // Dorado medio claro
            300: '#e5c78a',  // Dorado medio
            400: '#d1a96e',  // Dorado fuerte
            500: '#c9a26e',  // Dorado principal
            600: '#a7855b',  // Dorado oscuro
            700: '#806646',  // Dorado muy oscuro
          },
          teal: {
            50: '#e6fcfd',   // Verde azulado muy claro
            100: '#bff7f8',  // Verde azulado claro
            200: '#87eff0',  // Verde azulado medio claro
            300: '#4ee2e6',  // Verde azulado medio
            400: '#22cad1',  // Verde azulado fuerte
            500: '#00A4A8',  // Verde azulado principal
            600: '#008284',  // Verde azulado oscuro
            700: '#006265',  // Verde azulado muy oscuro
          },
        },
        success: {
          50: '#f0fdf4',
          500: '#22c55e',
          700: '#15803d',
        },
        warning: {
          50: '#fffbeb',
          500: '#f59e0b',
          700: '#b45309',
        },
        danger: {
          50: '#fef2f2',
          500: '#ef4444',
          700: '#b91c1c',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        display: ['Poppins', 'system-ui', 'sans-serif'],
      },
      spacing: {
        '72': '18rem',
        '84': '21rem',
        '96': '24rem',
      },
      borderRadius: {
        'sm': '0.125rem',
        DEFAULT: '0.25rem',
        'md': '0.375rem',
        'lg': '0.5rem',
        'xl': '0.75rem',
        '2xl': '1rem',
      },
      boxShadow: {
        'sm': '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
        DEFAULT: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1)',
        'md': '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1)',
        'lg': '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -4px rgba(0, 0, 0, 0.1)',
      },
      container: {
        center: true,
        padding: {
          DEFAULT: '1rem',
          sm: '2rem',
          lg: '4rem',
          xl: '5rem',
        },
      },
      width: {
        'sidebar': '16rem',
      },
      zIndex: {
        'sidebar': '40',
      },
      transitionProperty: {
        'sidebar': 'width, transform',
      }
    },
  },
  plugins: [
    require('@tailwindcss/forms')
  ]
}
