<template>
  <footer class="text-center py-1.5 px-4 bg-(--color-nav-bg) text-(--color-text-muted) text-xs border-t border-(--color-border)">
    <p>&copy; {{ year }} FAR-OUT Launch. <a href="https://faroutlaunch.org" target="_blank" class="text-(--color-text-muted)">faroutlaunch.org</a></p>
  </footer>
</template>

<script setup lang="ts">
const year = new Date().getFullYear()
</script>
