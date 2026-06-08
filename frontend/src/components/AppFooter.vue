<template>
  <footer>
    <p>&copy; {{ year }} FAR-OUT Launch. <a href="https://faroutlaunch.org" target="_blank">faroutlaunch.org</a></p>
  </footer>
</template>

<script setup lang="ts">
const year = new Date().getFullYear()
</script>

<style scoped>
footer {
  text-align: center;
  padding: 0.4rem 1rem;
  background-color: var(--color-nav-bg);
  color: var(--color-text-muted);
  font-size: 0.78rem;
  border-top: 1px solid var(--color-border);
}

footer a {
  color: var(--color-text-muted);
}
</style>
