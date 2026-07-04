import { useEffect, useRef, useState } from 'react'

export default function UserMenu({ user, onLogout }) {
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef(null)

  useEffect(() => {
    if (!isOpen) return

    function handleOutsideClick(event) {
      if (containerRef.current && !containerRef.current.contains(event.target)) {
        setIsOpen(false)
      }
    }

    document.addEventListener('click', handleOutsideClick)
    return () => document.removeEventListener('click', handleOutsideClick)
  }, [isOpen])

  return (
    <div className="user-menu" ref={containerRef}>
      <button
        type="button"
        className="user-chip"
        onClick={(e) => {
          e.stopPropagation()
          setIsOpen((prev) => !prev)
        }}
      >
        {user?.name || 'User'}
      </button>

      {isOpen ? (
        <div className="user-menu-dropdown">
          <p>{user?.name || 'User'}</p>
          <p>{user?.email}</p>
          <button type="button" className="link-button" onClick={onLogout}>
            Logout
          </button>
        </div>
      ) : null}
    </div>
  )
}
