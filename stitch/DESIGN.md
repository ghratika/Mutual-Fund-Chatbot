---
name: Emerald Zenith
colors:
  surface: '#0f131d'
  surface-dim: '#0f131d'
  surface-bright: '#353944'
  surface-container-lowest: '#0a0e18'
  surface-container-low: '#171b26'
  surface-container: '#1c1f2a'
  surface-container-high: '#262a35'
  surface-container-highest: '#313540'
  on-surface: '#dfe2f1'
  on-surface-variant: '#bbcabf'
  inverse-surface: '#dfe2f1'
  inverse-on-surface: '#2c303b'
  outline: '#86948a'
  outline-variant: '#3c4a42'
  surface-tint: '#4edea3'
  primary: '#4edea3'
  on-primary: '#003824'
  primary-container: '#10b981'
  on-primary-container: '#00422b'
  inverse-primary: '#006c49'
  secondary: '#adc6ff'
  on-secondary: '#002e6a'
  secondary-container: '#0566d9'
  on-secondary-container: '#e6ecff'
  tertiary: '#68dba9'
  on-tertiary: '#003825'
  tertiary-container: '#3eb686'
  on-tertiary-container: '#00422c'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#6ffbbe'
  primary-fixed-dim: '#4edea3'
  on-primary-fixed: '#002113'
  on-primary-fixed-variant: '#005236'
  secondary-fixed: '#d8e2ff'
  secondary-fixed-dim: '#adc6ff'
  on-secondary-fixed: '#001a42'
  on-secondary-fixed-variant: '#004395'
  tertiary-fixed: '#85f8c4'
  tertiary-fixed-dim: '#68dba9'
  on-tertiary-fixed: '#002114'
  on-tertiary-fixed-variant: '#005137'
  background: '#0f131d'
  on-background: '#dfe2f1'
  surface-variant: '#313540'
  surface-card: '#1E293B'
  text-primary: '#F8FAFC'
  text-secondary: '#94A3B8'
  accent-teal: '#059669'
  border-subtle: rgba(255, 255, 255, 0.08)
  glass-fill: rgba(30, 41, 59, 0.7)
typography:
  headline-xl:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
    letterSpacing: 0.04em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  container-max: 1200px
  gutter: 24px
  margin-mobile: 16px
  margin-desktop: 48px
---

## Brand & Style
The design system is engineered for a premium Mutual Fund FAQ Assistant, balancing the trustworthiness of traditional finance with the innovative energy of modern fintech. The brand personality is professional, secure, and forward-thinking, aimed at investors who value clarity and sophistication.

The visual style leverages **Glassmorphism** and **Minimalism**. By using semi-transparent layers, subtle backdrop blurs, and high-precision typography, the interface evokes a sense of depth and digital craftsmanship. The "Wealth Gradient" (Emerald to Teal) serves as a visual metaphor for growth and prosperity, while the deep slate foundations ensure high readability and reduced eye strain during deep financial research.

## Colors
This design system utilizes a dark-first color strategy to emphasize premium quality. 

- **Primary & Tertiary:** An Emerald-to-Teal gradient is the hallmark of the system, used exclusively for primary actions and growth indicators.
- **Secondary:** Electric Blue is reserved for informational cues, links, and secondary interactive states to differentiate from the "growth" emerald.
- **Surface Strategy:** The background uses a Deep Charcoal (#0B0F19). Cards and containers utilize a semi-transparent Slate (#1E293B at 70% opacity) to achieve a glassmorphic effect.
- **Typography Contrast:** Primary text uses Off-White (#F8FAFC) for maximum legibility, while Muted Grey (#94A3B8) is used for metadata and helper text to maintain a clear visual hierarchy.

## Typography
The system pairs **Outfit** for headlines with **Inter** for body and UI elements. 

**Outfit** provides a geometric, modern flair that feels tech-forward, used in larger sizes to create strong anchors for the page. **Inter** is used for its exceptional legibility in data-heavy environments, ensuring that financial terminology and assistant responses are easy to digest. 

Maintain tight tracking (letter-spacing) on headlines to emphasize the premium "editorial" feel. Use `body-md` as the standard for assistant chat bubbles to ensure a comfortable reading rhythm.

## Layout & Spacing
This design system follows a **Fixed Grid** model for desktop to maintain a structured, centered focus suitable for an assistant-led experience.

- **Desktop:** 12-column grid, 1200px max-width, 24px gutters.
- **Tablet:** 8-column grid, fluid width, 24px margins.
- **Mobile:** 4-column grid, fluid width, 16px margins.

Spacing is based on an 8px linear scale. Large sections should be separated by 64px or 80px to lean into the Minimalist aesthetic and provide plenty of "breathing room" for complex financial data.

## Elevation & Depth
Depth is conveyed through **Glassmorphism** and **Ambient Shadows** rather than traditional elevation levels.

1.  **Base Layer:** The Deep Charcoal (#0B0F19) floor.
2.  **Glass Layer:** Semi-transparent cards (#1E293B at 70%) with a `20px` backdrop blur. These cards must feature a `1px` solid border using `border-subtle` to define the edges against the dark background.
3.  **Shadows:** Use a "Soft Glow" approach for active elements. Instead of black shadows, use a very low-opacity Emerald tint for primary buttons and a subtle Slate-Blue shadow for cards (`offset: 0 10px, blur: 30px, spread: -5px, color: rgba(0, 0, 0, 0.3)`).

## Shapes
The design system uses **Rounded** (0.5rem) geometry to strike a balance between friendly approachability and corporate precision.

- **Small Components:** Checkboxes and small tags use `rounded-md` (4px).
- **Standard UI:** Buttons and Input fields use `rounded` (8px).
- **Large Containers:** Content cards and Chat bubbles use `rounded-xl` (24px) to create a soft, modern container for text.

## Components
- **Buttons:** Primary buttons use the Emerald-to-Teal gradient with white text. Secondary buttons should be transparent with a `secondary_color` (Electric Blue) border.
- **Assistant Chat Bubbles:** The AI's responses should appear in the standard glassmorphic card style. User messages should have a slightly darker, solid background to differentiate "input" from "system response."
- **Input Fields:** Search and question bars should be large, with a `1px` border that glows with the Primary Accent color when focused. Use `Inter body-md` for placeholder text.
- **Chips/Tags:** Used for "Suggested Questions." These should be pill-shaped with a subtle Slate background and a 1px border.
- **Cards:** Used for Fund summaries or FAQ categories. Must include the `backdrop-filter: blur(20px)` and a subtle inner-glow on the top edge to simulate light hitting the glass.
- **Data Visuals:** Charts and graphs should exclusively use Emerald, Teal, and Electric Blue to maintain the limited, premium palette.