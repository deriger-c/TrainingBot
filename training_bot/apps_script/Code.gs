const SHEET_NAMES = {
  sessions: 'Workout Sessions',
  results: 'Exercise Results',
  goals: 'Goals',
  library: 'Exercise Library',
  progress: 'Progress',
  settings: 'Settings',
};

const HEADERS = {
  sessions: [
    'Session ID',
    'Date',
    'Start Time',
    'End Time',
    'Duration Minutes',
    'Manual Reported Duration Minutes',
    'Duration Source',
    'Duration Conflict',
    'Workout Type',
    'Body Weight',
    'Energy Level',
    'Sleep Hours',
    'Status',
    'Total Exercises',
    'Completed Exercises',
    'General Notes',
  ],
  results: [
    'Result ID',
    'Session ID',
    'Date',
    'Workout Type',
    'Exercise Order',
    'Exercise Name',
    'Block',
    'Planned Sets',
    'Planned Reps',
    'Planned Rest Seconds',
    'Actual Result',
    'Weight Used',
    'Difficulty Level',
    'RPE',
    'Pain Or Discomfort',
    'Notes',
    'Completed At',
    'Status',
    'RIR',
    'Reserve Seconds',
    'Technique OK',
    'Pain Level',
    'Progression Eligible',
    'Progression Status',
    'Progression Reason',
    'Recommendation',
    'Next Target',
    'Set Type',
    'Stop Reason',
    'Fall Count',
    'Variation',
    'Load Definition',
    'Comparable',
  ],
  goals: [
    'Goal ID',
    'Goal Name',
    'Category',
    'Target',
    'Current Result',
    'Status',
    'Created At',
    'Updated At',
    'Notes',
  ],
  library: [
    'Exercise ID',
    'Exercise Name',
    'Workout Type',
    'Block',
    'Order',
    'Planned Sets',
    'Planned Reps',
    'Rest Seconds',
    'Estimated Duration Minutes',
    'Technique Tips',
    'Input Example',
  ],
  progress: [
    'Exercise Name',
    'Last Result',
    'Best Result',
    'Last Date',
    'Total Times Done',
    'Notes',
    'Strict Max',
    'Progression Lock',
    'Next Target',
    'Last RIR',
    'Last Pain Level',
    'Recommendation',
    'Comparable Success Streak',
  ],
  settings: [
    'User ID',
    'Default Body Weight',
    'Show Timers',
    'Show Technique Tips',
    'Default Rest Seconds',
    'Language',
    'Show Estimated Timing',
  ],
};

const DEFAULT_GOALS = [
  ['Стойка лицом к стене', 'Skill', '60 секунд'],
  ['Pike Push Up', 'Strength', '4x8 clean reps'],
  ['HSPU Progression', 'Skill/Strength', 'выйти на partial wall HSPU'],
  ['Подтягивания', 'Strength', '+10kg на 6 повторений'],
  ['Брусья', 'Strength', '+10kg на 8 повторений'],
  ['L-Sit или пресс', 'Core', '30 секунд'],
  ['Боковые подъёмы', 'Shoulders', 'стабильные 3x20'],
];

function doGet(e) {
  try {
    authorizeRequest_(e);
    ensureAllSheets();
    const action = getAction_(e);
    if (action === 'history') return json_({ ok: true, items: getHistory_() });
    if (action === 'progress') return json_({ ok: true, items: getProgress_() });
    if (action === 'lastWorkout') return json_({ ok: true, item: getLastWorkout_() });
    if (action === 'goals') return json_({ ok: true, items: getGoals_() });
    if (action === 'getSettings') return json_({ ok: true, items: listRows_(SHEET_NAMES.settings, HEADERS.settings) });
    if (action === 'setup') return json_({ ok: true, message: 'Sheets are ready' });
    return json_({ ok: true, message: 'Training bot API is alive' });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.stack ? err.stack : err) });
  }
}

function doPost(e) {
  try {
    authorizeRequest_(e);
    ensureAllSheets();
    const action = getAction_(e);
    const payload = parsePayload_(e);
    if (action === 'saveWorkoutSession') return json_({ ok: true, item: upsertObject_(SHEET_NAMES.sessions, HEADERS.sessions, 'Session ID', payload) });
    if (action === 'saveWorkoutBundle') return json_({ ok: true, item: saveWorkoutBundle_(payload) });
    if (action === 'saveExerciseResult') {
      const existed = resultExists_(payload);
      const saved = upsertObject_(SHEET_NAMES.results, HEADERS.results, 'Result ID', payload);
      if (!existed) updateProgressFromResult_(payload);
      return json_({ ok: true, item: saved });
    }
    if (action === 'saveProgress') return json_({ ok: true, item: saveProgress_(payload) });
    if (action === 'saveGoal') return json_({ ok: true, item: saveGoal_(payload) });
    if (action === 'updateGoal') return json_({ ok: true, item: updateGoal_(payload) });
    if (action === 'deleteGoal') return json_({ ok: true, deleted: deleteGoal_(payload) });
    if (action === 'saveSettings') return json_({ ok: true, item: saveSettings_(payload) });
    return json_({ ok: false, error: 'Unknown action: ' + action });
  } catch (err) {
    return json_({ ok: false, error: String(err && err.stack ? err.stack : err) });
  }
}

function authorizeRequest_(e) {
  const expected = PropertiesService.getScriptProperties().getProperty('BOT_SECRET');
  if (!expected) return;
  const provided = e && e.parameter && e.parameter.secret ? String(e.parameter.secret) : '';
  if (provided !== expected) throw new Error('Unauthorized');
}

function saveWorkoutBundle_(payload) {
  const lock = LockService.getScriptLock();
  lock.waitLock(30000);
  try {
    const session = payload.session || payload.Session || {};
    const results = payload.results || payload.Results || [];
    if (!session || !valueByHeader_(session, 'Session ID')) throw new Error('session with Session ID is required');
    if (!Array.isArray(results)) throw new Error('results must be an array');

    upsertObject_(SHEET_NAMES.sessions, HEADERS.sessions, 'Session ID', session);
    results.forEach((result) => {
      const existed = resultExists_(result);
      upsertObject_(SHEET_NAMES.results, HEADERS.results, 'Result ID', result);
      if (!existed) updateProgressFromResult_(result);
    });
    return { session, results_saved: results.length };
  } finally {
    lock.releaseLock();
  }
}

function ensureAllSheets() {
  ensureSheet_(SHEET_NAMES.sessions, HEADERS.sessions);
  ensureSheet_(SHEET_NAMES.results, HEADERS.results);
  ensureSheet_(SHEET_NAMES.goals, HEADERS.goals);
  ensureSheet_(SHEET_NAMES.library, HEADERS.library);
  ensureSheet_(SHEET_NAMES.progress, HEADERS.progress);
  ensureSheet_(SHEET_NAMES.settings, HEADERS.settings);
  seedGoalsIfEmpty_();
}

function ensureSheet_(name, headers) {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  let sheet = ss.getSheetByName(name);
  if (!sheet) sheet = ss.insertSheet(name);
  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headers);
    sheet.setFrozenRows(1);
    return sheet;
  }
  const current = sheet.getRange(1, 1, 1, Math.max(sheet.getLastColumn(), headers.length)).getValues()[0];
  const missing = headers.filter((header) => current.indexOf(header) === -1);
  if (missing.length > 0) {
    sheet.getRange(1, current.length + 1, 1, missing.length).setValues([missing]);
  }
  sheet.setFrozenRows(1);
  return sheet;
}

function getAction_(e) {
  return e && e.parameter && e.parameter.action ? e.parameter.action : '';
}

function parsePayload_(e) {
  if (!e || !e.postData || !e.postData.contents) return {};
  return JSON.parse(e.postData.contents);
}

function json_(data) {
  return ContentService
    .createTextOutput(JSON.stringify(data))
    .setMimeType(ContentService.MimeType.JSON);
}

function appendObject_(sheetName, headers, object) {
  const sheet = ensureSheet_(sheetName, headers);
  const actualHeaders = actualHeaders_(sheet, headers);
  const row = actualHeaders.map((header) => valueByHeader_(object, header));
  sheet.appendRow(row);
  return object;
}

function upsertObject_(sheetName, headers, keyHeader, object) {
  const sheet = ensureSheet_(sheetName, headers);
  const actualHeaders = actualHeaders_(sheet, headers);
  const keyValue = valueByHeader_(object, keyHeader);
  if (!keyValue) throw new Error(keyHeader + ' is required');
  const rowIndex = findRowByValue_(sheet, actualHeaders, keyHeader, keyValue);
  const row = actualHeaders.map((header) => valueByHeader_(object, header));
  if (rowIndex < 2) {
    sheet.appendRow(row);
  } else {
    sheet.getRange(rowIndex, 1, 1, actualHeaders.length).setValues([row]);
  }
  return object;
}

function actualHeaders_(sheet, fallbackHeaders) {
  const width = Math.max(sheet.getLastColumn(), fallbackHeaders.length);
  return sheet.getRange(1, 1, 1, width).getValues()[0].filter((header) => header !== '');
}

function valueByHeader_(object, header) {
  if (Object.prototype.hasOwnProperty.call(object, header)) return object[header];
  const snake = header.toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '');
  if (Object.prototype.hasOwnProperty.call(object, snake)) return object[snake];
  return '';
}

function listRows_(sheetName, headers) {
  const sheet = ensureSheet_(sheetName, headers);
  const actualHeaders = actualHeaders_(sheet, headers);
  const lastRow = sheet.getLastRow();
  if (lastRow < 2) return [];
  const values = sheet.getRange(2, 1, lastRow - 1, actualHeaders.length).getValues();
  return values
    .filter((row) => row.some((cell) => cell !== ''))
    .map((row) => rowToObject_(actualHeaders, row));
}

function rowToObject_(headers, row) {
  const item = {};
  headers.forEach((header, index) => {
    item[header] = row[index];
  });
  return item;
}

function getHistory_() {
  const items = listRows_(SHEET_NAMES.sessions, HEADERS.sessions);
  return items.reverse().slice(0, 10);
}

function getLastWorkout_() {
  const items = getHistory_();
  return items.length ? items[0] : null;
}

function getGoals_() {
  return listRows_(SHEET_NAMES.goals, HEADERS.goals);
}

function seedGoalsIfEmpty_() {
  const sheet = ensureSheet_(SHEET_NAMES.goals, HEADERS.goals);
  if (sheet.getLastRow() > 1) return;
  const now = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
  const rows = DEFAULT_GOALS.map((goal, index) => [
    'goal-default-' + (index + 1),
    goal[0],
    goal[1],
    goal[2],
    '',
    'active',
    now,
    now,
    'Стандартная цель',
  ]);
  sheet.getRange(2, 1, rows.length, HEADERS.goals.length).setValues(rows);
}

function saveGoal_(payload) {
  const goal = normalizeGoal_(payload);
  appendObject_(SHEET_NAMES.goals, HEADERS.goals, goal);
  return goal;
}

function normalizeGoal_(payload) {
  const now = Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm:ss');
  return {
    'Goal ID': valueByHeader_(payload, 'Goal ID') || 'goal-' + Utilities.getUuid().slice(0, 8),
    'Goal Name': valueByHeader_(payload, 'Goal Name'),
    'Category': valueByHeader_(payload, 'Category'),
    'Target': valueByHeader_(payload, 'Target'),
    'Current Result': valueByHeader_(payload, 'Current Result'),
    'Status': valueByHeader_(payload, 'Status') || 'active',
    'Created At': valueByHeader_(payload, 'Created At') || now,
    'Updated At': valueByHeader_(payload, 'Updated At') || now,
    'Notes': valueByHeader_(payload, 'Notes'),
  };
}

function updateGoal_(payload) {
  const goalId = payload.goal_id || payload['Goal ID'];
  if (!goalId) throw new Error('goal_id is required');
  const updates = payload.updates || {};
  const sheet = ensureSheet_(SHEET_NAMES.goals, HEADERS.goals);
  const row = findRowByValue_(sheet, HEADERS.goals, 'Goal ID', goalId);
  if (row < 2) throw new Error('Goal not found: ' + goalId);
  Object.keys(updates).forEach((key) => {
    const column = HEADERS.goals.indexOf(key) + 1;
    if (column > 0) sheet.getRange(row, column).setValue(updates[key]);
  });
  return rowToObject_(HEADERS.goals, sheet.getRange(row, 1, 1, HEADERS.goals.length).getValues()[0]);
}

function deleteGoal_(payload) {
  const goalId = payload.goal_id || payload['Goal ID'];
  if (!goalId) throw new Error('goal_id is required');
  const sheet = ensureSheet_(SHEET_NAMES.goals, HEADERS.goals);
  const row = findRowByValue_(sheet, HEADERS.goals, 'Goal ID', goalId);
  if (row < 2) throw new Error('Goal not found: ' + goalId);
  sheet.deleteRow(row);
  return true;
}

function saveSettings_(payload) {
  const sheet = ensureSheet_(SHEET_NAMES.settings, HEADERS.settings);
  const userId = String(valueByHeader_(payload, 'User ID'));
  if (!userId) throw new Error('User ID is required');
  let row = findRowByValue_(sheet, HEADERS.settings, 'User ID', userId);
  const normalized = {};
  HEADERS.settings.forEach((header) => normalized[header] = valueByHeader_(payload, header));
  if (row < 2) {
    appendObject_(SHEET_NAMES.settings, HEADERS.settings, normalized);
  } else {
    HEADERS.settings.forEach((header, index) => {
      sheet.getRange(row, index + 1).setValue(normalized[header]);
    });
  }
  return normalized;
}

function findRowByValue_(sheet, headers, header, value) {
  const actualHeaders = actualHeaders_(sheet, headers);
  const column = actualHeaders.indexOf(header) + 1;
  if (column < 1 || sheet.getLastRow() < 2) return -1;
  const values = sheet.getRange(2, column, sheet.getLastRow() - 1, 1).getValues();
  for (let i = 0; i < values.length; i += 1) {
    if (String(values[i][0]) === String(value)) return i + 2;
  }
  return -1;
}

function resultExists_(result) {
  const resultId = valueByHeader_(result, 'Result ID');
  if (!resultId) return false;
  const sheet = ensureSheet_(SHEET_NAMES.results, HEADERS.results);
  return findRowByValue_(sheet, HEADERS.results, 'Result ID', resultId) >= 2;
}

function updateProgressFromResult_(result) {
  const exerciseName = valueByHeader_(result, 'Exercise Name');
  const actualResult = valueByHeader_(result, 'Actual Result');
  const date = valueByHeader_(result, 'Date');
  if (!exerciseName || !actualResult || actualResult === 'skipped') return;

  const sheet = ensureSheet_(SHEET_NAMES.progress, HEADERS.progress);
  const row = findRowByValue_(sheet, HEADERS.progress, 'Exercise Name', exerciseName);
  if (row < 2) {
    const progressionEligible = String(valueByHeader_(result, 'Progression Eligible')).toLowerCase() === 'true';
    appendObject_(SHEET_NAMES.progress, HEADERS.progress, {
      'Exercise Name': exerciseName,
      'Last Result': actualResult,
      'Best Result': actualResult,
      'Last Date': date,
      'Total Times Done': 1,
      'Notes': '',
      'Progression Lock': String(valueByHeader_(result, 'Progression Eligible')).toLowerCase() === 'false' && Number(valueByHeader_(result, 'Pain Level') || 0) > 0,
      'Next Target': valueByHeader_(result, 'Next Target'),
      'Last RIR': valueByHeader_(result, 'RIR'),
      'Last Pain Level': valueByHeader_(result, 'Pain Level'),
      'Recommendation': valueByHeader_(result, 'Recommendation'),
      'Comparable Success Streak': progressionEligible ? 1 : 0,
    });
    return;
  }

  const values = sheet.getRange(row, 1, 1, HEADERS.progress.length).getValues()[0];
  const current = rowToObject_(HEADERS.progress, values);
  const best = chooseBestResult_(current['Best Result'], actualResult);
  const progressionEligible = String(valueByHeader_(result, 'Progression Eligible')).toLowerCase() === 'true';
  const previousStreak = Number(current['Comparable Success Streak'] || 0);
  const nextStreak = progressionEligible ? previousStreak + 1 : 0;
  setProgressValue_(sheet, row, 'Last Result', actualResult);
  setProgressValue_(sheet, row, 'Best Result', best);
  setProgressValue_(sheet, row, 'Last Date', date);
  setProgressValue_(sheet, row, 'Total Times Done', Number(current['Total Times Done'] || 0) + 1);
  setProgressValue_(sheet, row, 'Last RIR', valueByHeader_(result, 'RIR'));
  setProgressValue_(sheet, row, 'Last Pain Level', valueByHeader_(result, 'Pain Level'));
  setProgressValue_(sheet, row, 'Recommendation', valueByHeader_(result, 'Recommendation'));
  setProgressValue_(sheet, row, 'Next Target', valueByHeader_(result, 'Next Target'));
  setProgressValue_(sheet, row, 'Progression Lock', String(valueByHeader_(result, 'Progression Eligible')).toLowerCase() === 'false' && Number(valueByHeader_(result, 'Pain Level') || 0) > 0);
  setProgressValue_(sheet, row, 'Comparable Success Streak', nextStreak);
}

function setProgressValue_(sheet, row, header, value) {
  const column = actualHeaders_(sheet, HEADERS.progress).indexOf(header) + 1;
  if (column > 0 && value !== '') sheet.getRange(row, column).setValue(value);
}

function getProgress_() {
  return listRows_(SHEET_NAMES.progress, HEADERS.progress);
}

function saveProgress_(payload) {
  return upsertObject_(SHEET_NAMES.progress, HEADERS.progress, 'Exercise Name', payload);
}

function chooseBestResult_(oldResult, newResult) {
  if (!oldResult) return newResult;
  return scoreResult_(newResult) >= scoreResult_(oldResult) ? newResult : oldResult;
}

function scoreResult_(text) {
  if (!text) return 0;
  const matches = String(text).match(/[+\-]?\d+(?:[.,]\d+)?/g);
  if (!matches) return 0;
  return matches.reduce((sum, value) => sum + Number(String(value).replace(',', '.')), 0);
}
