<!-- STACK_PROFILE: {"backend": "node/express", "frontend": "react", "database": "sqlite"} -->

# Shadow Tasks: Private Productivity
==============================

## Core Data Models
-------------------

### Task Model

*   **Title**: String (max 100 characters)
*   **Status**: Enum (active, shadow)
*   **Priority**: Enum (void, high, normal)

```markdown
// task.model.ts
export enum Priority {
    VOID,
    HIGH,
    NORMAL,
}

export enum Status {
    ACTIVE,
    SHADOW,
}
```

### User Model

*   **Username**: String (max 100 characters)
*   **Password**: Hashed string
*   **Email**: Email address
*   **Tasks**: Array of Task IDs

```markdown
// user.model.ts
export class User {
    id: string;
    username: string;
    password: string;
    email: string;
    tasks: Task[];
}
```

## API Endpoints
-----------------

### Tasks Endpoint

*   `POST /tasks`: Create new task
	+ Request Body: `title` (String), `status` (Status Enum), `priority` (Priority Enum)
	+ Response: Created task object
*   `GET /tasks`: Retrieve list of tasks for current user
	+ Query Parameters: `status` (Status Enum), `priority` (Priority Enum)
	+ Response: Array of task objects

```markdown
// routes.ts
import { Router } from 'express';
import { Task, Status, Priority } from './task.model';

const router = Router();

router.post('/tasks', async (req, res) => {
    const task = await createTask(req.body.title, req.body.status, req.body.priority);
    return res.json(task);
});

router.get('/tasks', async (req, res) => {
    const tasks = await getTasksForUser(req.user.id);
    return res.json(tasks);
});
```

## State Machines
------------------

*   **Task Status**: Transition from `active` to `shadow` when marked as completed

```markdown
// task.state.ts
enum TaskState {
    ACTIVE,
    SHADOW,
}

class TaskStateMachine {
    transitionFromActiveToShadow(task: Task): void {
        // implement logic here
    }
}
```

## Necessary 3rd Party Integrations
-----------------------------------

*   **Digital Twin Integration**: Integrate with external digital twin platform to retrieve user data and task assignments

```markdown
// digital-twin.ts
import { DigitalTwinClient } from '@digital-twin-sdk/client';

const client = new DigitalTwinClient({
    apiKey: 'YOUR_API_KEY',
});

async function retrieveUserData(userId: string): Promise<any> {
    const userData = await client.getUserData(userId);
    return userData;
}
```

## Database Schema
-------------------

*   **Tasks Table**:
	+ `id`: Integer (Primary Key)
	+ `title`: String (max 100 characters)
	+ `status`: Status Enum
	+ `priority`: Priority Enum

```markdown
// migrations.ts
import { Sequelize } from 'sequelize';

const sequelize = new Sequelize({
    dialect: 'sqlite',
    storage: './shadow-tasks.db',
});

export const TasksTable = sequelize.define('tasks', {
    title: {
        type: DataTypes.STRING(100),
        allowNull: false,
    },
    status: {
        type: DataTypes.ENUM(...Object.values(Status)),
        allowNull: false,
    },
    priority: {
        type: DataTypes.ENUM(...Object.values(Priority)),
        allowNull: false,
    },
});
```

## API Reference
----------------

### Tasks Endpoint

*   `POST /tasks`
	+ Request Body:
		- `title`: String (max 100 characters)
		- `status`: Status Enum
		- `priority`: Priority Enum
	+ Response:

```markdown
// api-reference.ts
export const tasksEndpoint = {
    method: 'POST',
    path: '/tasks',
    summary: 'Create new task',
    requestBody: {
        required: true,
        content: {
            'application/json': {
                schema: {
                    type: 'object',
                    properties: {
                        title: { type: 'string', maxLength: 100 },
                        status: { enum: Object.values(Status) },
                        priority: { enum: Object.values(Priority) },
                    },
                },
            },
        },
    },
    responses: {
        201: {
            description: 'Task created',
            content: {
                'application/json': {
                    schema: {
                        type: 'object',
                        properties: {
                            id: { type: 'integer' },
                            title: { type: 'string', maxLength: 100 },
                            status: { enum: Object.values(Status) },
                            priority: { enum: Object.values(Priority) },
                        },
                    },
                },
            },
        },
    },
};
```

## Documentation (README.md)
---------------------------

```markdown
# Shadow Tasks: Private Productivity

### First Time Setup

1. Clone the repository using `git clone`
2. Install dependencies using `npm install`
3. Create a SQLite database using `sqlite3 shadow-tasks.db`
4. Run migrations using `npx sequelize-cli db:migrate`

### Digital Twin Integration

1. Obtain an API key from the digital twin platform
2. Configure the `digital-twin.ts` file with your API key
3. Integrate the digital twin client with your application
```