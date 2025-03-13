export const validators = {
  email: (email) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  },

  password: (password) => {
    // At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$/;
    return passwordRegex.test(password);
  },

  name: (name) => {
    return name.length >= 2 && name.length <= 50;
  },

  message: (message) => {
    return message.trim().length > 0 && message.length <= 5000;
  },

  conversationTitle: (title) => {
    return title.trim().length > 0 && title.length <= 100;
  }
};

export const getValidationMessage = (field, value) => {
  switch (field) {
    case 'email':
      return validators.email(value) ? '' : 'Please enter a valid email address';
    case 'password':
      return validators.password(value)
        ? ''
        : 'Password must be at least 8 characters long and contain at least one uppercase letter, one lowercase letter, and one number';
    case 'name':
      return validators.name(value) ? '' : 'Name must be between 2 and 50 characters';
    case 'message':
      return validators.message(value) ? '' : 'Message must not be empty and must be less than 5000 characters';
    case 'conversationTitle':
      return validators.conversationTitle(value) ? '' : 'Title must not be empty and must be less than 100 characters';
    default:
      return '';
  }
}; 