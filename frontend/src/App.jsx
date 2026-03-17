import { useEffect, useState } from 'react'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import TransactionReplay from './pages/TransactionReplay'
import { getPaymentHistory, listPaymentUsers, loginPaymentUser, savePaymentHistory } from './services/api'

function App() {
  const [authLoading, setAuthLoading] = useState(false)
  const [user, setUser] = useState(null)
  const [view, setView] = useState('login')
  const [transactions, setTransactions] = useState([])
  const [selectedTransaction, setSelectedTransaction] = useState(null)
  const [users, setUsers] = useState([])

  useEffect(() => {
    listPaymentUsers()
      .then((allUsers) => {
        const mappedUsers = allUsers.map((entry) => ({
          ...entry,
          otpEnabled: entry.otp_enabled,
        }))
        setUsers(mappedUsers)
      })
      .catch(() => {
        setUsers([])
      })
  }, [])

  const onLogin = async ({ username, password }) => {
    setAuthLoading(true)
    try {
      const [authenticatedUser, allUsers, history] = await Promise.all([
        loginPaymentUser(username, password),
        listPaymentUsers(),
        getPaymentHistory(100),
      ])

      const mappedUsers = allUsers.map((entry) => ({
        ...entry,
        otpEnabled: entry.otp_enabled,
      }))
      const mappedHistory = history.map((entry) => ({
        id: String(entry.id),
        time: new Date(entry.created_at).toLocaleTimeString(),
        date: new Date(entry.created_at).toLocaleDateString(),
        senderName: entry.sender_name,
        senderUpi: entry.sender_upi,
        senderPort: entry.sender_port,
        receiverName: entry.receiver_name,
        receiverUpi: entry.receiver_upi,
        receiverPort: entry.receiver_port,
        amount: String(entry.amount),
        note: entry.note,
        algorithm: entry.algorithm,
        decision: entry.decision,
        otpVerified: entry.otp_verified,
        risk: entry.risk,
        leakage: entry.leakage,
        baseAttack: entry.base_attack,
        correlation: entry.correlation,
        defense: entry.defense,
        attackerEnabled: entry.attacker_enabled,
        attackerPort: entry.attacker_port,
        theftAmount: entry.theft_amount,
        senderOtpEnabled: entry.sender_otp_enabled,
        receiverOtpEnabled: entry.receiver_otp_enabled,
        reasons: entry.reasons || [],
        timeline: entry.timeline || [],
      }))

      setUser({ ...authenticatedUser, otpEnabled: authenticatedUser.otp_enabled })
      setUsers(mappedUsers)
      setTransactions(mappedHistory)
      setView('dashboard')
    } catch {
      setAuthLoading(false)
      throw new Error('Invalid username or password.')
    }
    setAuthLoading(false)
  }

  const onLogout = () => {
    setUser(null)
    setUsers([])
    setTransactions([])
    setSelectedTransaction(null)
    setView('login')
  }

  const onAddTransaction = async (transaction) => {
    const payload = {
      sender_user_id: transaction.senderUserId,
      sender_name: transaction.senderName,
      sender_upi: transaction.senderUpi,
      sender_port: transaction.senderPort,
      receiver_user_id: transaction.receiverUserId,
      receiver_name: transaction.receiverName,
      receiver_upi: transaction.receiverUpi,
      receiver_port: transaction.receiverPort,
      amount: Number(transaction.amount),
      note: transaction.note,
      algorithm: transaction.algorithm,
      decision: transaction.decision,
      otp_verified: transaction.otpVerified,
      risk: Number(transaction.risk),
      leakage: Number(transaction.leakage),
      base_attack: Number(transaction.baseAttack),
      correlation: Number(transaction.correlation),
      defense: Boolean(transaction.defense),
      attacker_enabled: Boolean(transaction.attackerEnabled),
      attacker_port: Number(transaction.attackerPort),
      theft_amount: Number(transaction.theftAmount || 0),
      sender_otp_enabled: Boolean(transaction.senderOtpEnabled),
      receiver_otp_enabled: Boolean(transaction.receiverOtpEnabled),
      reasons: transaction.reasons || [],
      timeline: transaction.timeline || [],
    }

    const response = await savePaymentHistory(payload)
    const entry = response.record
    const mapped = {
      id: String(entry.id),
      time: new Date(entry.created_at).toLocaleTimeString(),
      date: new Date(entry.created_at).toLocaleDateString(),
      senderName: entry.sender_name,
      senderUpi: entry.sender_upi,
      senderPort: entry.sender_port,
      receiverName: entry.receiver_name,
      receiverUpi: entry.receiver_upi,
      receiverPort: entry.receiver_port,
      amount: String(entry.amount),
      note: entry.note,
      algorithm: entry.algorithm,
      decision: entry.decision,
      otpVerified: entry.otp_verified,
      risk: entry.risk,
      leakage: entry.leakage,
      baseAttack: entry.base_attack,
      correlation: entry.correlation,
      defense: entry.defense,
      attackerEnabled: entry.attacker_enabled,
      attackerPort: entry.attacker_port,
      theftAmount: entry.theft_amount,
      senderOtpEnabled: entry.sender_otp_enabled,
      receiverOtpEnabled: entry.receiver_otp_enabled,
      reasons: entry.reasons || [],
      timeline: entry.timeline || [],
    }
    setTransactions((prev) => [mapped, ...prev])
  }

  const onOpenReplay = (transaction) => {
    setSelectedTransaction(transaction)
    setView('replay')
  }

  const onBackToDashboard = () => {
    setView('dashboard')
  }

  if (!user || view === 'login') {
    return <Login onLogin={onLogin} loading={authLoading} users={users} />
  }

  if (view === 'replay') {
    return <TransactionReplay transaction={selectedTransaction} onBack={onBackToDashboard} />
  }

  return (
    <Dashboard
      transactions={transactions}
      onAddTransaction={onAddTransaction}
      onOpenReplay={onOpenReplay}
      user={user}
      onLogout={onLogout}
      users={users}
    />
  )
}

export default App
