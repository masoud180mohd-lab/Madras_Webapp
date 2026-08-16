allprojects {
    repositories {
        google()
        mavenCentral()
    }
}

val newBuildDir: Directory =
    rootProject.layout.buildDirectory
        .dir("../../build")
        .get()
rootProject.layout.buildDirectory.value(newBuildDir)

subprojects {
    val newSubprojectBuildDir: Directory = newBuildDir.dir(project.name)
    project.layout.buildDirectory.value(newSubprojectBuildDir)
}

// AGP 9 locks compileSdk after evaluation, so afterEvaluate is too late.
// finalizeDsl runs after each library's android {} block and before lock.
// Register this BEFORE evaluationDependsOn(":app").
subprojects {
    pluginManager.withPlugin("com.android.library") {
        extensions
            .findByType(com.android.build.api.variant.LibraryAndroidComponentsExtension::class.java)
            ?.finalizeDsl { extension ->
                extension.compileSdk = 36
            }
    }
}

subprojects {
    project.evaluationDependsOn(":app")
}

tasks.register<Delete>("clean") {
    delete(rootProject.layout.buildDirectory)
}
