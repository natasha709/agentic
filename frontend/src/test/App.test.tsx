import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import axios from 'axios'
import App from '../App'

// Mock axios
vi.mock('axios')

describe('App Component', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(axios.get).mockResolvedValue({ data: {} })
    vi.mocked(axios.post).mockResolvedValue({ 
      data: { response: 'Test response', messages: [], confirmation: null } 
    })
  })

  it('renders the application title', () => {
    render(<App />)
    // Use getAllByText since there are multiple elements with "Sentinel AI"
    expect(screen.getAllByText(/Sentinel AI/i).length).toBeGreaterThan(0)
  })

  it('has a chat input field', () => {
    render(<App />)
    const input = screen.getByPlaceholderText(/Describe your IT issue/i)
    expect(input).toBeInTheDocument()
  })

  it('has a send button', () => {
    render(<App />)
    // The send button exists but may be disabled
    const buttons = screen.getAllByRole('button')
    expect(buttons.length).toBeGreaterThan(0)
  })

  it('allows typing in the input field', async () => {
    const user = userEvent.setup()
    render(<App />)
    
    const input = screen.getByPlaceholderText(/Describe your IT issue/i)
    await user.type(input, 'Hello, I need help')
    
    expect(input).toHaveValue('Hello, I need help')
  })

  it('clears input after sending message', async () => {
    const user = userEvent.setup()
    
    render(<App />)
    
    const input = screen.getByPlaceholderText(/Describe your IT issue/i)
    const buttons = screen.getAllByRole('button')
    // Find the send button (should be the one with Send icon or last button)
    const sendButton = buttons[buttons.length - 1]
    
    await user.type(input, 'Test message')
    await user.click(sendButton)
    
    await waitFor(() => {
      expect(input).toHaveValue('')
    })
  })

  it('displays error message on API failure', async () => {
    const user = userEvent.setup()
    
    // Mock axios post to throw an error
    vi.mocked(axios.post).mockRejectedValue(new Error('Network error'))
    
    render(<App />)
    
    const input = screen.getByPlaceholderText(/Describe your IT issue/i)
    const buttons = screen.getAllByRole('button')
    const sendButton = buttons[buttons.length - 1]
    
    await user.type(input, 'Test message')
    await user.click(sendButton)
    
    await waitFor(() => {
      expect(screen.getAllByText(/error/i).length).toBeGreaterThan(0)
    })
  })
})
