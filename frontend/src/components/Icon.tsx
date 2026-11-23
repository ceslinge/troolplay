const PATHS = {
  eye: (
    <>
      <path d="M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  path: (
    <>
      <path d="M6 21c0-4 4-5 6-7s1-5 4-7 4-3 4-3" />
      <circle cx="5" cy="21" r="1" />
    </>
  ),
  mask: <path d="M5 4h14v7a7 7 0 01-14 0zM9 9.5h.01M15 9.5h.01M9 14c2 1.5 4 1.5 6 0" />,
  compass: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M15.5 8.5l-2 5-5 2 2-5z" />
    </>
  ),
  chain: <path d="M10 7H7a4 4 0 000 8h3M14 7h3a4 4 0 010 8h-3M11 4l-1 3M13 20l1-3" />,
  bubbles: <path d="M3 5h12v8H8l-4 3v-3H3zM18 9h3v7h-1v3l-3-3h-5" />,
  quill: <path d="M20 3c-7 1-12 6-14 13l-1 4 4-1c7-2 12-7 13-14zM6 18l7-7" />,
  pin: (
    <>
      <path d="M12 21s-7-6-7-11a7 7 0 0114 0c0 5-7 11-7 11z" />
      <circle cx="12" cy="10" r="2.5" />
    </>
  ),
  crossed: <path d="M4 20L20 4M15 4h5v5M4 4l6 6M14 14l6 6M20 15v5h-5" />,
}

export type IconName = keyof typeof PATHS

type Props = {
  name: IconName
  size?: number
}

function Icon({ name, size = 20 }: Props) {
  return (
    <svg
      viewBox="0 0 24 24"
      width={size}
      height={size}
      fill="none"
      stroke="currentColor"
      strokeWidth={1.8}
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      {PATHS[name]}
    </svg>
  )
}

export default Icon
