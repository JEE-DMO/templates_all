
---

# Maven Wrapper – Migration and Usage Guide

## Table of contents

1. Context
2. Migration for Existing Projects
3. Using the Maven Wrapper
4. Maven Wrapper Files Overview
5. Updating the Maven Version
6. Industry Adoption
7. Summary

---

## 1. Context

Historically, most projects have been built using a locally installed version of Apache Maven.

Example:

```text
mvn clean install
```

To improve build reproducibility and ensure consistent environments across developers and CI pipelines, projects should use the **Maven Wrapper**.

The Maven Wrapper allows Maven to run **without requiring a local Maven installation** and guarantees that all environments use the same Maven version.

---

## 2. Migration for Existing Projects

For existing projects, migrating to the Maven Wrapper requires only a few steps.

### Generate the Maven Wrapper

Run the following command at the root of the project:

```text
mvn wrapper:wrapper
```

You can also specify the Maven version during generation:

```text
mvn wrapper:wrapper -Dmaven=3.9.9
```

This ensures that the project immediately uses the expected Maven version.

### Verify Generated Files

The following files will be created:

```text
mvnw
mvnw.cmd
.mvn/
  wrapper/
    maven-wrapper.jar
    maven-wrapper.properties
```

These files must be **committed to the repository**.

### Commit the Wrapper

Example:

```text
git add mvnw mvnw.cmd .mvn/
git commit -m "Add Maven Wrapper"
```

---

## 3. Using the Maven Wrapper

After migration, Maven commands should be executed using the wrapper.

Instead of:

```text
mvn clean install
```

use:

```text
./mvnw clean install
```

Examples:

```text
./mvnw clean install
./mvnw test
./mvnw package
```

---

## 4. Maven Wrapper Files Overview

The wrapper introduces several files in the project.

```text
mvnw
mvnw.cmd
.mvn/
  wrapper/
    maven-wrapper.jar
    maven-wrapper.properties
```

**mvnw**

Shell script used to run Maven on Linux and macOS.

Example:

```text
./mvnw clean install
```

**mvnw.cmd**

Command script used to run Maven on Windows environments.

Example:

```text
mvnw.cmd clean install
```

**.mvn/wrapper/maven-wrapper.jar**

Internal component used by the wrapper to download and execute the correct Maven version.

This file should not be modified manually.

**.mvn/wrapper/maven-wrapper.properties**

Defines the Maven version used by the project.

Example:

```properties
distributionUrl=https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.9.9/apache-maven-3.9.9-bin.zip
```

---

## 5. Updating the Maven Version

The Maven version is defined in:

```text
.mvn/wrapper/maven-wrapper.properties
```

To update the version, modify the `distributionUrl`.

Example:

```properties
distributionUrl=https://repo.maven.apache.org/maven2/org/apache/maven/apache-maven/3.9.10/apache-maven-3.9.10-bin.zip
```

The next execution of the wrapper will automatically download and use the new version.

---

## 6. Internal & Industry Adoption

The Maven Wrapper is widely adopted in modern Java projects.

Projects generated with Spring Initializr include the Maven Wrapper by default, which has been standard practice in the Spring Boot ecosystem for several years. This reflects a broader industry trend toward reproducible builds and standardized development environments.

Several internal teams also reference the Maven Wrapper in their engineering documentation. These pages confirm that the approach described here is aligned with practices already used across the organization.

Examples of internal references:

- [Data Platform Build Guidelines](https://confluence.company.net/display/PLATFORM/build-guidelines)
- [Engineering Build Standards](https://confluence.company.net/display/ENG/build-standards)
- [Java Development Best Practices](https://confluence.company.net/display/JAVA/dev-best-practices)

Although these pages mention the Maven Wrapper, **the present documentation should be considered the reference for our projects**, as it provides the migration steps and usage conventions specifically adapted to our environment.

---

## 7. Summary

Recommended practices:

* generate the Maven Wrapper for all Maven projects
* commit wrapper files to the repository
* execute builds using `./mvnw` instead of `mvn`
* manage Maven versions through `maven-wrapper.properties`

---
