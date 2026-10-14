<!-- 统一的线性图标组件：使用本地 SVG 路径，避免额外的图标依赖和网络请求。 -->
<template>
  <svg class="app-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
    <path v-for="(path, index) in paths[name] || paths.chat" :key="index" :d="path" />
  </svg>
</template>

<script setup>
defineProps({ name: { type: String, default: 'chat' } })

const paths = {
  user: ['M16 7a4 4 0 1 1-8 0 4 4 0 0 1 8 0Z', 'M4 21v-2a8 8 0 0 1 16 0v2'],
  support: ['M4 13v-2a8 8 0 0 1 16 0v2', 'M4 12H2v7h4v-7H4Zm16 0h2v7h-4v-7h2ZM20 19v2h-6'],
  chat: ['M21 11.5a8.5 8.5 0 0 1-8.5 8.5H4l-2 2V11.5a9.5 9.5 0 0 1 19 0Z', 'M7 9h9M7 13h6'],
  book: ['M12 5v16M12 5C9 3 5 3 2 4v15c3-1 7-1 10 2 3-3 7-3 10-2V4c-3-1-7-1-10 1Z'],
  chart: ['M4 3v17h17M9 15v-4M14 15V7M19 15V4'],
  plus: ['M12 5v14M5 12h14'],
  arrow: ['M7 17 17 7M7 7h10v10'],
  send: ['M12 19V5M6 11l6-6 6 6'],
  chevron: ['m9 5 7 7-7 7'],
  refresh: ['M20 7v5h-5M4 17v-5h5', 'M6.1 6a8 8 0 0 1 13 2M4.9 16a8 8 0 0 0 13 2'],
  activity: ['M3 12h4l3-8 4 16 3-8h4'],
  settings: ['M4 7h16M4 17h16M9 4v6M15 14v6'],
  shield: ['M12 3 3 7v5c0 5 9 9 9 9s9-4 9-9V7l-9-4Z', 'm8 12 3 3 5-6'],
  search: ['M20 20l-5-5', 'M17 10a7 7 0 1 1-14 0 7 7 0 0 1 14 0Z'],
  upload: ['M12 16V3M7 8l5-5 5 5M4 15v6h16v-6'],
  receipt: ['M6 3h12v19l-3-2-3 2-3-2-3 2V3Z', 'M9 8h6M9 12h6'],
  code: ['m8 7-5 5 5 5m8-10 5 5-5 5M14 4l-4 16'],
  return: ['M9 4 4 9l5 5M4 9h10a6 6 0 0 1 0 12'],
  check: ['m5 12 4 4L19 6'],
  info: ['M12 11v6M12 7h.01', 'M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z']
}
</script>
