const express = require('express');
const router = express.Router();
const logsController = require('../controllers/logsController');
const authMiddleware = require('../middleware/auth');

// All logs routes require authentication
router.use(authMiddleware);

// Get logs with pagination and filters
router.get('/', logsController.getLogs);

// Get unique categories
router.get('/categories', logsController.getCategories);

// Export logs
router.get('/export', logsController.exportLogs);

// Clear logs
router.delete('/', logsController.clearLogs);

module.exports = router;