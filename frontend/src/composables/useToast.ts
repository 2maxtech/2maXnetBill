import { ref } from 'vue'

const message = ref('')
const visible = ref(false)
let timeout: number

export function useToast() {
  function show(msg: string, duration = 3500) {
    message.value = msg
    visible.value = true
    clearTimeout(timeout)
    timeout = window.setTimeout(() => { visible.value = false }, duration)
  }

  return { message, visible, show }
}
