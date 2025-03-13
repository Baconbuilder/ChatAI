class InactivityTimer {
  constructor(timeout = 30000, onTimeout) {
    this.timeout = timeout;
    this.onTimeout = onTimeout;
    this.timer = null;
    this.resetTimer = this.resetTimer.bind(this);
    this.setupEventListeners();
  }

  setupEventListeners() {
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
      document.addEventListener(event, this.resetTimer);
    });
  }

  resetTimer() {
    if (this.timer) {
      clearTimeout(this.timer);
    }
    this.timer = setTimeout(() => {
      if (this.onTimeout) {
        this.onTimeout();
      }
    }, this.timeout);
  }

  start() {
    this.resetTimer();
  }

  stop() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  cleanup() {
    this.stop();
    ['mousedown', 'mousemove', 'keypress', 'scroll', 'touchstart'].forEach(event => {
      document.removeEventListener(event, this.resetTimer);
    });
  }
}

export default InactivityTimer; 