function toggleDropdown(id, btn) {
  const dropdown = document.getElementById(id);
  const isHidden = dropdown.classList.contains('hidden');

  if (isHidden) {
    dropdown.classList.remove('hidden');
    btn.setAttribute('aria-expanded', 'true');
  } else {
    dropdown.classList.add('hidden');
    btn.setAttribute('aria-expanded', 'false');
  }
}

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('quick-add-form');
  const message = document.getElementById('quick-add-message');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const amount = parseFloat(document.getElementById('expense-amount').value);
    const desc = document.getElementById('expense-desc').value.trim();
    const category = document.getElementById('expense-category').value;

    if (!amount || amount <= 0) {
      message.textContent = 'Please enter a valid amount.';
      message.style.color = 'red';
      return;
    }

    if (!desc) {
      message.textContent = 'Please enter a description.';
      message.style.color = 'red';
      return;
    }

    if (!category) {
      message.textContent = 'Please select a category.';
      message.style.color = 'red';
      return;
    }

    try {
      message.textContent = 'Adding expense...';
      message.style.color = 'black';

      setTimeout(() => {
        message.textContent = 'Expense added successfully!';
        message.style.color = 'green';
        form.reset();
      }, 1000);
    } catch (err) {
      message.textContent = 'Error adding expense.';
      message.style.color = 'red';
    }
  });

  loadAISuggestions();
});

async function loadAISuggestions() {
  const container = document.getElementById('ai-suggestions-container');
  
  setTimeout(() => {
    container.innerHTML = `
      <ul>
        <li>Try reducing dining out expenses by 15% next month.</li>
        <li>Consider setting a monthly grocery budget of Rs. 3000.</li>
        <li>Your savings goal is on track — keep it up!</li>
      </ul>
    `;
  }, 1500);
}

function renderAISuggestions(suggestions) {
  const container = document.getElementById('ai-suggestions-container');
  if (!suggestions.length) {
    container.innerHTML = '<p>No suggestions available yet.</p>';
    return;
  }
  const ul = document.createElement('ul');
  suggestions.forEach((s) => {
    const li = document.createElement('li');
    li.textContent = s;
    ul.appendChild(li);
  });
  container.innerHTML = '';
  container.appendChild(ul);
}
