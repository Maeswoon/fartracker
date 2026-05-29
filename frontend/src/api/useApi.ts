import { ref } from 'vue'

export function useApi<T>() {
  const data = ref<T | null>(null) as ReturnType<typeof ref<T | null>>
  const loading = ref(true)
  const error = ref<string | null>(null)

  async function execute(fn: () => Promise<T>) {
    loading.value = true
    error.value = null
    try {
      data.value = await fn()
    } catch {
      error.value = 'Failed to load data'
    } finally {
      loading.value = false
    }
  }

  return { data, loading, error, execute }
}

export function useForm() {
  const success = ref(false)
  const error = ref<string | null>(null)

  async function submit(fn: () => Promise<void>, errorMsg = 'Failed to submit') {
    success.value = false
    error.value = null
    try {
      await fn()
      success.value = true
    } catch {
      error.value = errorMsg
    }
  }

  return { success, error, submit }
}
