const { pool } = require('../config/database');
const logger = require('../utils/logger');

class LogsController {
  // Get logs with pagination and filters
  async getLogs(req, res) {
    try {
      const {
        page = 1,
        limit = 50,
        level,
        category,
        search,
        startDate,
        endDate,
        userId
      } = req.query;

      const offset = (page - 1) * limit;
      const conditions = ['1=1'];
      const params = [];

      // Build filter conditions
      if (level) {
        params.push(level);
        conditions.push(`level = $${params.length}`);
      }

      if (category) {
        params.push(category);
        conditions.push(`category = $${params.length}`);
      }

      if (search) {
        params.push(`%${search}%`);
        conditions.push(`message ILIKE $${params.length}`);
      }

      if (startDate) {
        params.push(startDate);
        conditions.push(`timestamp >= $${params.length}`);
      }

      if (endDate) {
        params.push(endDate);
        conditions.push(`timestamp <= $${params.length}`);
      }

      if (userId || req.user?.id) {
        params.push(userId || req.user.id);
        conditions.push(`user_id = $${params.length}`);
      }

      // Get total count
      const countQuery = `
        SELECT COUNT(*) 
        FROM logs 
        WHERE ${conditions.join(' AND ')}
      `;
      const countResult = await pool.query(countQuery, params);
      const total = parseInt(countResult.rows[0].count, 10);

      // Get logs
      params.push(limit);
      params.push(offset);
      const logsQuery = `
        SELECT 
          id,
          timestamp,
          level,
          category,
          message,
          metadata,
          user_id,
          session_id
        FROM logs 
        WHERE ${conditions.join(' AND ')}
        ORDER BY timestamp DESC
        LIMIT $${params.length - 1} OFFSET $${params.length}
      `;

      const logsResult = await pool.query(logsQuery, params);

      res.json({
        logs: logsResult.rows,
        total,
        page: parseInt(page, 10),
        limit: parseInt(limit, 10)
      });
    } catch (error) {
      logger.error('Error fetching logs', { error: error.message });
      res.status(500).json({ error: 'Failed to fetch logs' });
    }
  }

  // Get unique categories
  async getCategories(req, res) {
    try {
      const query = `
        SELECT DISTINCT category 
        FROM logs 
        WHERE user_id = $1
        ORDER BY category
      `;
      const result = await pool.query(query, [req.user?.id]);
      const categories = result.rows.map(row => row.category);
      res.json(categories);
    } catch (error) {
      logger.error('Error fetching categories', { error: error.message });
      res.status(500).json({ error: 'Failed to fetch categories' });
    }
  }

  // Clear logs
  async clearLogs(req, res) {
    try {
      const { level, category, startDate, endDate } = req.body;
      const conditions = ['user_id = $1'];
      const params = [req.user?.id];

      if (level) {
        params.push(level);
        conditions.push(`level = $${params.length}`);
      }

      if (category) {
        params.push(category);
        conditions.push(`category = $${params.length}`);
      }

      if (startDate) {
        params.push(startDate);
        conditions.push(`timestamp >= $${params.length}`);
      }

      if (endDate) {
        params.push(endDate);
        conditions.push(`timestamp <= $${params.length}`);
      }

      const query = `
        DELETE FROM logs 
        WHERE ${conditions.join(' AND ')}
      `;

      await pool.query(query, params);
      res.json({ message: 'Logs cleared successfully' });
    } catch (error) {
      logger.error('Error clearing logs', { error: error.message });
      res.status(500).json({ error: 'Failed to clear logs' });
    }
  }

  // Export logs
  async exportLogs(req, res) {
    try {
      const {
        level,
        category,
        search,
        startDate,
        endDate
      } = req.query;

      const conditions = ['user_id = $1'];
      const params = [req.user?.id];

      // Build filter conditions (same as getLogs)
      if (level) {
        params.push(level);
        conditions.push(`level = $${params.length}`);
      }

      if (category) {
        params.push(category);
        conditions.push(`category = $${params.length}`);
      }

      if (search) {
        params.push(`%${search}%`);
        conditions.push(`message ILIKE $${params.length}`);
      }

      if (startDate) {
        params.push(startDate);
        conditions.push(`timestamp >= $${params.length}`);
      }

      if (endDate) {
        params.push(endDate);
        conditions.push(`timestamp <= $${params.length}`);
      }

      const query = `
        SELECT 
          id,
          timestamp,
          level,
          category,
          message,
          metadata,
          user_id,
          session_id
        FROM logs 
        WHERE ${conditions.join(' AND ')}
        ORDER BY timestamp DESC
      `;

      const result = await pool.query(query, params);

      // Set response headers for download
      res.setHeader('Content-Type', 'application/json');
      res.setHeader(
        'Content-Disposition',
        `attachment; filename="logs_${new Date().toISOString().split('T')[0]}.json"`
      );

      res.json(result.rows);
    } catch (error) {
      logger.error('Error exporting logs', { error: error.message });
      res.status(500).json({ error: 'Failed to export logs' });
    }
  }
}

module.exports = new LogsController();