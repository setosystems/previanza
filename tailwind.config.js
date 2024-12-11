module.exports = {
  darkMode: 'class',
  content: [
    "./templates/**/*.html",
    "./static/**/*.js"
  ],
  logLevel: 'silent',
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
        secondary: {
          50: '#f4f7fb',   // Gris azulado muy claro
          100: '#e9eef6',  // Gris azulado claro
          200: '#d0ddee',  // Gris azulado medio claro
          300: '#a6bddf',  // Gris azulado medio
          400: '#749ac8',  // Gris azulado fuerte
          500: '#4A78B0',  // Gris azulado principal (secondary)
          600: '#3A5E8C',  // Gris azulado oscuro
          700: '#2C4768',  // Gris azulado muy oscuro
          800: '#1F3246',  // Gris azulado profundo
          900: '#141E2A',  // Gris azulado casi negro
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
        green: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
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
        'row': '2.5rem',
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
        'header': '0 1px 3px 0 rgba(0, 0, 0, 0.05)',
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
        'header': '30',
      },
      position: {
        'sticky': 'sticky',
        'fixed': 'fixed',
      },
      transitionProperty: {
        'sidebar': 'width, transform',
      },
      height: {
        'screen': '100vh',
        'full': '100%'
      },
      minHeight: {
        'screen': '100vh',
        'full': '100%'
      },
      backgroundColor: theme => ({
        ...theme('colors'),
        dark: {
          'primary': '#1a1f2e',
          'secondary': '#252b3b',
          'hover': '#2d3548'
        }
      }),
      textColor: theme => ({
        ...theme('colors'),
        dark: {
          'primary': '#f3f4f6',
          'secondary': '#d1d5db'
        }
      }),
      ringColor: {
        'search': {
          focus: '#60a5fa',
        }
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-in-out',
        'slide-in': 'slideIn 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideIn: {
          '0%': { transform: 'translateY(-10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [
    require('@tailwindcss/forms'),
    function({ addUtilities }) {
      const iconUtilities = {
        '.table-cell': {
          'padding-top': '0.5rem',
          'padding-bottom': '0.5rem',
          'padding-left': '1rem',
          'padding-right': '1rem',
          'height': 'theme("spacing.row")',
          'white-space': 'nowrap',
          'vertical-align': 'middle'
        },
        '.material-icon': {
          'font-family': '"Material Symbols Rounded"',
          'font-weight': 'normal',
          'font-style': 'normal',
          'font-size': '24px',
          'line-height': '1',
          'letter-spacing': 'normal',
          'text-transform': 'none',
          'display': 'inline-block',
          'white-space': 'nowrap',
          'word-wrap': 'normal',
          'direction': 'ltr',
          '-webkit-font-smoothing': 'antialiased'
        },
        '.material-icon-outlined': {
          'font-family': '"Material Symbols Outlined"',
        }
      }
      addUtilities(iconUtilities)
    }
  ]
}
