// Render Chart.js
const ctx = document.getElementById('cieChart').getContext('2d');
const cieChart = new Chart(ctx, {
  type: 'bar',
  data: {
    labels: ['Test-1 (25)', 'Test-2 (25)', 'Lab CIE (50)', 'Total CIE (50)'],
    datasets: [{
      label: 'Marks Scored',
      data: [18, 20, 42, 40],
      backgroundColor: ['#3b82f6', '#3b82f6', '#6366f1', '#10b981']
    }]
  },
  options: { scales: { y: { beginAtZero: true, max: 50 } } }
});

function calculateCIE() {
  const t1 = parseFloat(document.getElementById('test1').value) || 0;
  const t2 = parseFloat(document.getElementById('test2').value) || 0;
  const lab = parseFloat(document.getElementById('labCie').value) || 0;

  const total = ((t1 + t2) / 2) + (lab / 2);
  const isEligible = total >= 20;

  const resDiv = document.getElementById('cieResult');
  resDiv.style.backgroundColor = isEligible ? '#dcfce7' : '#fee2e2';
  resDiv.style.color = isEligible ? '#166534' : '#991b1b';
  resDiv.innerHTML = `Total CIE: ${total.toFixed(1)} / 50 <br> Status: ${isEligible ? '✅ Eligible for SEE' : '⚠️ Not Eligible (Below 20)'}`;

  // Update chart dynamically
  cieChart.data.datasets[0].data = [t1, t2, lab, total];
  cieChart.update();
}

const assignments = [
  { subject: 'CDD (1BCS303)', title: 'Exp 6: CI Actions', due: '2026-11-12', completed: false },
  { subject: 'Operating Systems', title: 'CPU Scheduling', due: '2026-11-05', completed: false }
];

function getBadge(dueDateStr, isCompleted) {
  if (isCompleted) return '<span class="badge badge-green">Green – Completed</span>';
  
  const today = new Date();
  today.setHours(0,0,0,0);
  const due = new Date(dueDateStr);
  const diffDays = Math.ceil((due - today) / (1000 * 60 * 60 * 24));

  if (diffDays < 0) return '<span class="badge badge-red">Red – Overdue</span>';
  if (diffDays === 0) return '<span class="badge badge-orange">Orange – Due Today</span>';
  if (diffDays <= 2) return '<span class="badge badge-yellow">Yellow – Due Soon</span>';
  return '<span class="badge badge-blue">Blue – Upcoming</span>';
}

function renderAssignments() {
  const tbody = document.getElementById('assignmentList');
  tbody.innerHTML = '';
  assignments.forEach((a, idx) => {
    tbody.innerHTML += `
      <tr>
        <td>${a.subject}</td>
        <td>${a.title}</td>
        <td>${a.due}</td>
        <td>${getBadge(a.due, a.completed)}</td>
        <td><button onclick="toggleDone(${idx})">${a.completed ? 'Undo' : 'Mark Done'}</button></td>
      </tr>
    `;
  });
}

function addAssignment() {
  const subject = document.getElementById('subjectSelect').value;
  const title = document.getElementById('assignTitle').value;
  const due = document.getElementById('dueDate').value;
  if (!title || !due) return alert('Please enter both title and due date');

  assignments.push({ subject, title, due, completed: false });
  renderAssignments();
}

function toggleDone(idx) {
  assignments[idx].completed = !assignments[idx].completed;
  renderAssignments();
}

// Initial render
renderAssignments();
calculateCIE();