/**
 * Superset API Response Validation Scripts
 * These scripts can be used in Postman/Apifox test tabs
 * or integrated into automated testing frameworks
 */

// ===========================================
// Common Test Utilities
// ===========================================

/**
 * Validate HTTP status code
 * @param {number} expectedStatus - Expected status code
 */
function validateStatus(expectedStatus = 200) {
    pm.test(`Status code is ${expectedStatus}`, function () {
        pm.response.to.have.status(expectedStatus);
    });
}

/**
 * Validate response time is within acceptable limits
 * @param {number} maxTime - Maximum acceptable response time in ms
 */
function validateResponseTime(maxTime = 5000) {
    pm.test(`Response time is less than ${maxTime}ms`, function () {
        pm.expect(pm.response.responseTime).to.be.below(maxTime);
    });
}

/**
 * Validate JSON response structure
 * @param {string[]} requiredFields - Array of required field names
 */
function validateJsonStructure(requiredFields = []) {
    pm.test('Response is valid JSON', function () {
        pm.response.to.be.json;
    });

    if (requiredFields.length > 0) {
        pm.test('Response has required fields', function () {
            const responseJson = pm.response.json();
            requiredFields.forEach(field => {
                pm.expect(responseJson).to.have.property(field);
            });
        });
    }
}

/**
 * Validate error response structure
 * @param {number} expectedStatus - Expected error status code
 */
function validateErrorResponse(expectedStatus) {
    pm.test(`Error response with status ${expectedStatus}`, function () {
        pm.response.to.have.status(expectedStatus);
        const responseJson = pm.response.json();
        pm.expect(responseJson).to.satisfy(function(response) {
            return response.hasOwnProperty('message') || 
                   response.hasOwnProperty('msg') ||
                   response.hasOwnProperty('error');
        });
    });
}

// ===========================================
// Authentication Validation
// ===========================================

/**
 * Validate login response and save tokens
 */
function validateLoginResponse() {
    validateStatus(200);
    validateResponseTime();
    
    pm.test('Login response contains access token', function () {
        const responseJson = pm.response.json();
        pm.expect(responseJson).to.have.property('access_token');
        pm.expect(responseJson.access_token).to.be.a('string');
        pm.expect(responseJson.access_token).to.not.be.empty;
        
        // Save token for subsequent requests
        pm.collectionVariables.set('accessToken', responseJson.access_token);
    });

    pm.test('Access token is valid JWT format', function () {
        const responseJson = pm.response.json();
        const token = responseJson.access_token;
        const tokenParts = token.split('.');
        pm.expect(tokenParts).to.have.lengthOf(3);
    });

    // Save refresh token if present
    pm.test('Save refresh token if available', function () {
        const responseJson = pm.response.json();
        if (responseJson.refresh_token) {
            pm.collectionVariables.set('refreshToken', responseJson.refresh_token);
        }
    });
}

/**
 * Validate user info response
 */
function validateUserInfoResponse() {
    validateStatus(200);
    validateJsonStructure(['result']);
    
    pm.test('User info contains required fields', function () {
        const responseJson = pm.response.json();
        const user = responseJson.result;
        pm.expect(user).to.have.property('username');
        pm.expect(user).to.have.property('email');
        pm.expect(user).to.have.property('roles');
        pm.expect(user.roles).to.be.an('array');
    });
}

// ===========================================
// Dashboard Validation
// ===========================================

/**
 * Validate dashboard list response
 */
function validateDashboardListResponse() {
    validateStatus(200);
    validateResponseTime();
    validateJsonStructure(['count', 'result']);
    
    pm.test('Dashboard list structure is valid', function () {
        const responseJson = pm.response.json();
        pm.expect(responseJson.count).to.be.a('number');
        pm.expect(responseJson.result).to.be.an('array');
    });

    pm.test('Dashboard objects have required fields', function () {
        const responseJson = pm.response.json();
        if (responseJson.result.length > 0) {
            const dashboard = responseJson.result[0];
            pm.expect(dashboard).to.have.property('id');
            pm.expect(dashboard).to.have.property('dashboard_title');
            pm.expect(dashboard).to.have.property('url');
            pm.expect(dashboard).to.have.property('published');
            
            // Save first dashboard ID for subsequent tests
            pm.collectionVariables.set('dashboardId', dashboard.id);
        }
    });
}

/**
 * Validate single dashboard response
 */
function validateDashboardDetailsResponse() {
    validateStatus(200);
    validateJsonStructure(['result']);
    
    pm.test('Dashboard details are complete', function () {
        const responseJson = pm.response.json();
        const dashboard = responseJson.result;
        pm.expect(dashboard).to.have.property('dashboard_title');
        pm.expect(dashboard).to.have.property('position_json');
        pm.expect(dashboard).to.have.property('metadata');
        pm.expect(dashboard).to.have.property('charts');
    });
}

// ===========================================
// Chart Validation
// ===========================================

/**
 * Validate chart list response
 */
function validateChartListResponse() {
    validateStatus(200);
    validateJsonStructure(['count', 'result']);
    
    pm.test('Chart list structure is valid', function () {
        const responseJson = pm.response.json();
        pm.expect(responseJson.result).to.be.an('array');
        
        if (responseJson.result.length > 0) {
            const chart = responseJson.result[0];
            pm.expect(chart).to.have.property('id');
            pm.expect(chart).to.have.property('slice_name');
            pm.expect(chart).to.have.property('viz_type');
            
            // Save first chart ID
            pm.collectionVariables.set('chartId', chart.id);
        }
    });
}

/**
 * Validate chart data response
 */
function validateChartDataResponse() {
    pm.test('Chart data request completed', function () {
        pm.response.to.have.status.oneOf([200, 202]);
    });
    
    pm.test('Chart data response structure', function () {
        const responseJson = pm.response.json();
        pm.expect(responseJson).to.have.property('result');
        
        if (Array.isArray(responseJson.result)) {
            responseJson.result.forEach(result => {
                pm.expect(result).to.have.property('status');
            });
        }
    });
}

// ===========================================
// Dataset Validation
// ===========================================

/**
 * Validate dataset list response
 */
function validateDatasetListResponse() {
    validateStatus(200);
    validateJsonStructure(['count', 'result']);
    
    pm.test('Dataset structure validation', function () {
        const responseJson = pm.response.json();
        if (responseJson.result.length > 0) {
            const dataset = responseJson.result[0];
            pm.expect(dataset).to.have.property('id');
            pm.expect(dataset).to.have.property('table_name');
            pm.expect(dataset).to.have.property('database');
            
            // Save first dataset ID
            pm.collectionVariables.set('datasetId', dataset.id);
        }
    });
}

// ===========================================
// Database Validation
// ===========================================

/**
 * Validate database list response
 */
function validateDatabaseListResponse() {
    validateStatus(200);
    validateJsonStructure(['result']);
    
    pm.test('Database objects validation', function () {
        const responseJson = pm.response.json();
        if (responseJson.result.length > 0) {
            const database = responseJson.result[0];
            pm.expect(database).to.have.property('id');
            pm.expect(database).to.have.property('database_name');
            pm.expect(database).to.have.property('sqlalchemy_uri_decrypted');
            
            // Save first database ID
            pm.collectionVariables.set('databaseId', database.id);
        }
    });
}

/**
 * Validate database connection test response
 */
function validateConnectionTestResponse() {
    pm.test('Connection test response received', function () {
        pm.response.to.have.status.oneOf([200, 400, 422]);
    });
    
    pm.test('Connection test has message', function () {
        const responseJson = pm.response.json();
        pm.expect(responseJson).to.have.property('message');
    });
}

// ===========================================
// SQL Lab Validation
// ===========================================

/**
 * Validate SQL execution response
 */
function validateSqlExecutionResponse() {
    pm.test('SQL execution completed', function () {
        pm.response.to.have.status.oneOf([200, 201, 202]);
    });
    
    pm.test('SQL execution result structure', function () {
        const responseJson = pm.response.json();
        pm.expect(responseJson).to.have.property('status');
        
        if (responseJson.status === 'success') {
            pm.expect(responseJson).to.have.property('data');
        }
    });
}

// ===========================================
// Security Validation
// ===========================================

/**
 * Validate roles list response
 */
function validateRolesListResponse() {
    validateStatus(200);
    validateJsonStructure(['result']);
    
    pm.test('Roles structure validation', function () {
        const responseJson = pm.response.json();
        pm.expect(responseJson.result).to.be.an('array');
        
        if (responseJson.result.length > 0) {
            const role = responseJson.result[0];
            pm.expect(role).to.have.property('id');
            pm.expect(role).to.have.property('name');
        }
    });
}

/**
 * Validate users list response
 */
function validateUsersListResponse() {
    validateStatus(200);
    validateJsonStructure(['result']);
    
    pm.test('Users data validation', function () {
        const responseJson = pm.response.json();
        if (responseJson.result.length > 0) {
            const user = responseJson.result[0];
            pm.expect(user).to.have.property('username');
            pm.expect(user).to.have.property('email');
            pm.expect(user).to.have.property('roles');
        }
    });
}

// ===========================================
// APEX JWT Validation
// ===========================================

/**
 * Validate APEX JWT login response
 */
function validateApexJwtLoginResponse() {
    pm.test('APEX JWT login response', function () {
        pm.response.to.have.status.oneOf([200, 404]);
    });
    
    if (pm.response.code === 200) {
        pm.test('APEX JWT token received', function () {
            const responseJson = pm.response.json();
            pm.expect(responseJson).to.have.property('token');
            pm.expect(responseJson.token).to.be.a('string');
            pm.collectionVariables.set('apexJwtToken', responseJson.token);
        });
    } else {
        pm.test('APEX endpoint not available (expected)', function () {
            pm.expect(pm.response.code).to.equal(404);
        });
    }
}

/**
 * Validate APEX token validation response
 */
function validateApexTokenValidationResponse() {
    pm.test('APEX token validation response', function () {
        pm.response.to.have.status.oneOf([200, 404]);
    });
    
    if (pm.response.code === 200) {
        pm.test('Token validation successful', function () {
            const responseJson = pm.response.json();
            pm.expect(responseJson).to.have.property('valid');
            pm.expect(responseJson.valid).to.be.true;
        });
    }
}

// ===========================================
// Health Check Validation
// ===========================================

/**
 * Validate health check response
 */
function validateHealthCheckResponse() {
    validateStatus(200);
    
    pm.test('Health check content validation', function () {
        const responseText = pm.response.text();
        pm.expect(responseText).to.include('OK');
    });
}

/**
 * Validate OpenAPI specification response
 */
function validateOpenApiResponse() {
    validateStatus(200);
    
    pm.test('OpenAPI specification structure', function () {
        const responseJson = pm.response.json();
        pm.expect(responseJson).to.have.property('openapi');
        pm.expect(responseJson).to.have.property('info');
        pm.expect(responseJson).to.have.property('paths');
    });
}

// ===========================================
// Performance and Load Testing
// ===========================================

/**
 * Validate performance metrics
 * @param {number} maxResponseTime - Maximum acceptable response time
 * @param {number} minThroughput - Minimum acceptable requests per second
 */
function validatePerformanceMetrics(maxResponseTime = 2000, minThroughput = 10) {
    pm.test(`Response time under ${maxResponseTime}ms`, function () {
        pm.expect(pm.response.responseTime).to.be.below(maxResponseTime);
    });
    
    // For concurrent tests, you might want to track throughput
    if (pm.iterationData) {
        pm.test('Throughput validation', function () {
            const startTime = pm.iterationData.get('startTime');
            const currentTime = Date.now();
            const duration = (currentTime - startTime) / 1000; // seconds
            const requestCount = pm.iterationData.get('requestCount') || 1;
            const throughput = requestCount / duration;
            
            pm.expect(throughput).to.be.above(minThroughput);
        });
    }
}

// ===========================================
// Utility Functions
// ===========================================

/**
 * Save response data to collection variables
 * @param {Object} mappings - Object mapping response paths to variable names
 */
function saveResponseData(mappings) {
    const responseJson = pm.response.json();
    
    Object.keys(mappings).forEach(jsonPath => {
        const variableName = mappings[jsonPath];
        const value = getValueByPath(responseJson, jsonPath);
        if (value !== undefined) {
            pm.collectionVariables.set(variableName, value);
        }
    });
}

/**
 * Get value from response JSON by dot notation path
 * @param {Object} obj - JSON object
 * @param {string} path - Dot notation path (e.g., 'result.0.id')
 */
function getValueByPath(obj, path) {
    return path.split('.').reduce((current, key) => {
        if (current && current.hasOwnProperty(key)) {
            return current[key];
        }
        return undefined;
    }, obj);
}

/**
 * Generate test report summary
 */
function generateTestSummary() {
    const testResults = pm.response.json();
    
    pm.test('Generate test summary', function () {
        console.log('=== Test Summary ===');
        console.log(`Response Time: ${pm.response.responseTime}ms`);
        console.log(`Status Code: ${pm.response.code}`);
        console.log(`Response Size: ${pm.response.responseSize} bytes`);
        
        if (testResults.result && Array.isArray(testResults.result)) {
            console.log(`Result Count: ${testResults.result.length}`);
        }
        
        console.log('===================');
    });
}

// ===========================================
// Export for Node.js environments
// ===========================================

if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        validateStatus,
        validateResponseTime,
        validateJsonStructure,
        validateErrorResponse,
        validateLoginResponse,
        validateUserInfoResponse,
        validateDashboardListResponse,
        validateDashboardDetailsResponse,
        validateChartListResponse,
        validateChartDataResponse,
        validateDatasetListResponse,
        validateDatabaseListResponse,
        validateConnectionTestResponse,
        validateSqlExecutionResponse,
        validateRolesListResponse,
        validateUsersListResponse,
        validateApexJwtLoginResponse,
        validateApexTokenValidationResponse,
        validateHealthCheckResponse,
        validateOpenApiResponse,
        validatePerformanceMetrics,
        saveResponseData,
        getValueByPath,
        generateTestSummary
    };
} 