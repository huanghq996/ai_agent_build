<template>
  <main class="p-4">
    <h1 class="text-xl font-semibold">Demo: Health Check</h1>
    <p class="mt-2 text-sm text-gray-600">status: {{ state.status }}</p>
    <p class="text-sm text-gray-600">time: {{ state.time }}</p>
  </main>
</template>

<script>
import { onMounted, reactive } from "vue";
import { getHealth } from "./api/generated/index.js";

export default {
  name: "App",
  setup() {
    const state = reactive({ status: "loading", time: "-" });
    onMounted(async () => {
      const data = await getHealth();
      state.status = data.status;
      state.time = data.time;
    });
    return { state };
  },
};
</script>
