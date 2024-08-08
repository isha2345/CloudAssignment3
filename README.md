# CI/CD pipeline (part 3) - Orchestration and CRUD
- Step 1: Clone the repository
- Step 2: For building Docker images, run the following command:
  ```
  docker-compose -f docker-compose.test.yml build
  ```
- Step 3: For starting Docker containers, run the following command:
  ```
  docker-compose -f docker-compose.test.yml up -d
  ```
- Step 4: For Running the tests, run the following command:
  ```
  docker-compose -f docker-compose.test.yml run test
  ```
