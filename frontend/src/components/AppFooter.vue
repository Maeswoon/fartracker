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
  padding: 1rem;
  background-color: #333;
  color: #ccc;
  font-size: 0.9rem;
  border-top: 1px solid #555;
}

footer a {
  color: #aaa;
}
</style>
