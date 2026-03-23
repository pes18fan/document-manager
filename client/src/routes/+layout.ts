// Disable server side rendering. This makes the application slower but allows
// usage of Node.js functions on the frontend. This is necessary to access the
// FileList interface on the "/upload" route.
// NOTE: If anyone can find a workaround for the above that avoids disabling SSR,
// please do make use of it because this option causes significant slowdown.
export const ssr = false;
