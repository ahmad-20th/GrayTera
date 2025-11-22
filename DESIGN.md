# GrayTera - Design Pattern Documentation

> **Project:** GrayTera - Advanced Pentesting Automation Tool  
> **Architecture:** Modular DAST (Dynamic Application Security Testing)  
> **Last Updated:** November 2025

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Design Patterns Used](#design-patterns-used)
3. [Pattern 1: Pipeline Pattern](#pattern-1-pipeline-pattern)
4. [Pattern 2: Strategy Pattern](#pattern-2-strategy-pattern)
5. [Pattern 3: Observer Pattern](#pattern-3-observer-pattern)
6. [Pattern 4: Registry Pattern](#pattern-4-registry-pattern)
7. [Pattern 5: Template Method Pattern](#pattern-5-template-method-pattern)
8. [Why These Patterns?](#why-these-patterns)
9. [Alternative Patterns Considered](#alternative-patterns-considered)
10. [Pattern Interactions](#pattern-interactions)

---

## Architecture Overview

GrayTera follows a **modular, pipeline-based architecture** designed for extensibility and maintainability. The system processes security testing through three main stages:

```
┌─────────────────────────────────────────────────────────────┐
│                    GrayTera Architecture                     │
└─────────────────────────────────────────────────────────────┘

                    ┌──────────────────┐
                    │   CLI Interface   │
                    │    (main.py)     │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │    Pipeline       │◄──── Observer Pattern
                    │   Orchestrator    │      (Logging, Progress)
                    └────────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │  Stage 1 │      │  Stage 2 │      │  Stage 3 │
    │Subdomain │      │   Vuln   │      │  Exploit │
    │   Enum   │      │   Scan   │      │          │
    └──────────┘      └────┬─────┘      └────┬─────┘
                           │                  │
                           ▼                  ▼
                    ┌─────────────┐    ┌─────────────┐
                    │  Scanners   │    │  Exploits   │
                    │  (Strategy) │    │ (Strategy)  │
                    └─────────────┘    └─────────────┘
                           │                  │
                           └────────┬─────────┘
                                    ▼
                            ┌───────────────┐
                            │  Data Store   │
                            │ (Persistence) │
                            └───────────────┘
```

### Key Design Goals

1. **Modularity**: Each component is independent and replaceable
2. **Extensibility**: Easy to add new scanners/exploits without modifying core
3. **Maintainability**: Clear separation of concerns
4. **Testability**: Each component can be tested in isolation
5. **Team Collaboration**: 8 developers can work on different modules simultaneously

---

## Design Patterns Used

| Pattern | Purpose | Location |
|---------|---------|----------|
| **Pipeline** | Sequential stage execution | `core/pipeline.py` |
| **Strategy** | Interchangeable scanners/exploits | `scanners/`, `exploits/` |
| **Observer** | Event notification & logging | `observers/` |
| **Registry** | Dynamic scanner/exploit management | `*_registry.py` |
| **Template Method** | Common stage structure | `core/stage.py` |

---

## Pattern 1: Pipeline Pattern

### Intent
> Define a series of processing stages where each stage performs a specific operation and passes results to the next stage.

### Problem We're Solving

In penetration testing, tasks must happen in a specific order:
1. First, discover targets (subdomain enumeration)
2. Then, scan those targets for vulnerabilities
3. Finally, exploit discovered vulnerabilities

We need a way to:
- Execute stages sequentially
- Pass data between stages
- Handle failures gracefully
- Support pause/resume functionality
- Allow running specific stages independently

### Structure

```
┌────────────────────────────────────────────────────────────┐
│                     Pipeline Pattern                       │
└────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │   Pipeline   │
    │ Orchestrator │
    └──────┬───────┘
           │ manages
           │
    ┌──────▼───────────────────────────────────┐
    │                                          │
    │  stages: List[Stage]                     │
    │  current_stage_index: int                │
    │                                          │
    │  + run(target)                           │
    │  + pause()                               │
    │  + resume(target)                        │
    │  + _run_all_stages(target)               │
    │  + _run_specific_stage(target, name)     │
    └──────┬───────────────────────────────────┘
           │ contains
           │
    ┌──────▼────────┬──────────────┬──────────────┐
    │               │              │              │
┌───▼────────┐  ┌──▼─────────┐  ┌─▼──────────┐    │
│  Stage 1   │  │  Stage 2   │  │  Stage 3   │    │
│ Subdomain  │  │    Vuln    │  │  Exploit   │    │
│    Enum    │  │    Scan    │  │            │    │
└────────────┘  └────────────┘  └────────────┘    │
     │               │                │           │
     └───────────────┴────────────────┴───────────┘
                     │
                     ▼
              ┌──────────────┐
              │    Target    │
              │  (Data Flow) │
              └──────────────┘
```

### Implementation in GrayTera

**File: `core/pipeline.py`**

```python
class Pipeline:
    """Pipeline Orchestrator - manages sequential stage execution"""
    
    def __init__(self, data_store: DataStore, config_path: str):
        self.data_store = data_store
        self.stages = self._initialize_stages()
        self.current_stage_index = 0
    
    def _initialize_stages(self) -> List[Stage]:
        """Create pipeline stages in order"""
        return [
            SubdomainEnumStage(config),    # Stage 1
            VulnerabilityScanStage(config), # Stage 2
            ExploitationStage(config)       # Stage 3
        ]
    
    def run(self, domain: str):
        """Execute all stages in sequence"""
        target = Target(domain=domain)
        
        for idx, stage in enumerate(self.stages):
            self.current_stage_index = idx
            success = stage.execute(target)
            
            if not success:
                break  # Stop pipeline on failure
            
            self.data_store.save_target(target)  # Checkpoint
        
        return target
```

### Benefits

✅ **Sequential Execution**: Stages run in defined order  
✅ **Data Flow**: Each stage enriches the Target object  
✅ **Failure Handling**: Pipeline stops if a stage fails  
✅ **Checkpointing**: Save progress after each stage  
✅ **Stage Independence**: Stages don't know about each other

This is similar to the [**Chain of Responsibility**](https://refactoring.guru/design-patterns/chain-of-responsibility) pattern, but with **mandatory sequential processing** rather than optional handling.

### Real-World Analogy

Think of an assembly line in a car factory:
- Stage 1: Install engine
- Stage 2: Install wheels
- Stage 3: Paint car

Each stage **must** complete before the next begins. If Stage 1 fails (no engine), the car doesn't move to Stage 2.

---

## Pattern 2: Strategy Pattern

### Intent
> Define a family of algorithms, encapsulate each one, and make them interchangeable. Strategy lets the algorithm vary independently from clients that use it.

### Problem We're Solving

We need to support multiple vulnerability types (SQLi, XSS, CSRF, etc.), but:
- Each vulnerability requires different detection logic
- New vulnerability types should be easy to add
- Scanners should be interchangeable
- The scanning stage shouldn't need to change when adding new scanners

### Structure

```
┌────────────────────────────────────────────────────────────┐
│                     Strategy Pattern                       │
│               (Applied to Scanners & Exploits)             │
└────────────────────────────────────────────────────────────┘

         ┌──────────────────────────┐
         │  VulnerabilityScanStage  │
         │        (Context)         │
         └─────────┬────────────────┘
                   │ uses
                   │
         ┌─────────▼─────────────┐
         │   ScannerRegistry     │
         │                       │
         │ + get_all_scanners()  │
         └─────────┬─────────────┘
                   │ manages
                   │
         ┌─────────▼─────────────┐
         │   <<interface>>       │
         │    BaseScanner        │
         │                       │
         │ + scan(url): Vulns    │
         └─────────┬─────────────┘
                   │ implements
        ┌──────────┼──────────┬────────────┐
        │          │          │            │
    ┌───▼───┐  ┌──▼────┐  ┌──▼────┐  ┌───▼───┐
    │ SQLi  │  │  XSS  │  │ CSRF  │  │  XXE  │
    │Scanner│  │Scanner│  │Scanner│  │Scanner│
    └───────┘  └───────┘  └───────┘  └───────┘
    (Concrete Strategies)
```

### Implementation in GrayTera

**File: `scanners/base_scanner.py`**

```python
class BaseScanner(ABC):
    """Strategy Interface - defines scanner contract"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def scan(self, target_url: str) -> List[Vulnerability]:
        """
        Scan a target URL for vulnerabilities.
        Each concrete scanner implements its own algorithm.
        """
        pass
```

**File: `scanners/sqli_scanner.py`**

```python
class SQLiScanner(BaseScanner):
    """Concrete Strategy - implements SQLi detection algorithm"""
    
    def __init__(self):
        super().__init__("SQLi Scanner")
        self.payloads = ["'", "' OR '1'='1", "1' UNION SELECT NULL--"]
    
    def scan(self, target_url: str) -> List[Vulnerability]:
        """SQLi-specific scanning algorithm"""
        vulnerabilities = []
        
        for payload in self.payloads:
            if self._test_sqli(target_url, payload):
                vuln = Vulnerability(
                    vuln_type="sqli",
                    url=target_url,
                    payload=payload
                )
                vulnerabilities.append(vuln)
        
        return vulnerabilities
```

**File: `scanners/xss_scanner.py`**

```python
class XSSScanner(BaseScanner):
    """Another Concrete Strategy - implements XSS detection"""
    
    def __init__(self):
        super().__init__("XSS Scanner")
        self.payloads = ["<script>alert(1)</script>", "<img src=x>"]
    
    def scan(self, target_url: str) -> List[Vulnerability]:
        """XSS-specific scanning algorithm"""
        # Different algorithm, same interface
        # ...
```

**File: `stages/vulnerability_scan.py`**

```python
class VulnerabilityScanStage(Stage):
    """Context - uses strategies without knowing their details"""
    
    def execute(self, target: Target) -> bool:
        # Get all registered scanners
        scanners = self.scanner_registry.get_all_scanners()
        
        # Run each scanner (strategy) against targets
        for subdomain in target.subdomains:
            for scanner in scanners:
                vulnerabilities = scanner.scan(subdomain)
                target.vulnerabilities.extend(vulnerabilities)
        
        return True
```

### Benefits

✅ **Open/Closed Principle**: Add new scanners without modifying existing code  
✅ **Single Responsibility**: Each scanner handles one vulnerability type  
✅ **Flexibility**: Enable/disable scanners at runtime  
✅ **Testability**: Test each scanner independently  
✅ **Team Collaboration**: Different developers work on different scanners

Direct implementation of [**Strategy Pattern**](https://refactoring.guru/design-patterns/strategy)

### Real-World Analogy

Think of payment methods in an e-commerce app:
- You can pay with Credit Card, PayPal, or Bitcoin
- The checkout process (Context) doesn't care which you choose
- Each payment method (Strategy) implements its own processing logic
- Adding Apple Pay doesn't require changing the checkout code

In GrayTera:
- The scanning stage (checkout) doesn't care which scanners run
- Each scanner (payment method) implements its own detection logic
- Adding a new scanner doesn't require changing the scanning stage

---

## Pattern 3: Observer Pattern

### Intent
> Define a one-to-many dependency between objects so that when one object changes state, all its dependents are notified automatically.

### Problem We're Solving

We need to:
- Log events to console
- Write events to log files
- Track progress for users
- Generate reports from events
- **Without** tightly coupling these features to the core logic

Traditional approach (BAD):

```python
def execute(self, target):
    print("[*] Starting scan...")  # Console logging
    log_file.write("Starting scan...")  # File logging
    progress_bar.update(10)  # Progress tracking
    
    # Actual scanning logic buried in logging code
```

This creates **tight coupling** and makes testing difficult.

### Structure

```
┌────────────────────────────────────────────────────────────┐
│                     Observer Pattern                       │
└────────────────────────────────────────────────────────────┘

    ┌──────────────────┐
    │     Subject      │
    │   (Pipeline,     │
    │     Stages)      │
    ├──────────────────┤
    │ observers: []    │
    │ + attach(obs)    │
    │ + notify(event)  │◄──────┐
    └──────────────────┘       │
                               │ notifies
                               │
            ┌──────────────────┴────────────────┐
            │                                   │
    ┌───────▼────────┐                  ┌──────▼──────┐
    │ <<interface>>  │                  │             │
    │ BaseObserver   │                  │   Event     │
    ├────────────────┤                  │   Data      │
    │ + update(...)  │                  └─────────────┘
    └───────┬────────┘
            │ implements
    ┌───────┼────────┬────────────┐
    │       │        │            │
┌───▼───┐ ┌─▼──┐ ┌──▼────┐  ┌────▼────┐
│Console│ │File│ │Progress│ │ Report  │
│Observer│ │Obs│ │Observer│ │Observer │
└───────┘ └────┘ └────────┘ └─────────┘
(Concrete Observers)
```

### Implementation in GrayTera

**File: `observers/base_observer.py`**

```python
class BaseObserver(ABC):
    """Observer Interface"""
    
    @abstractmethod
    def update(self, stage: str, event: str, data: Any = None):
        """Called when subject emits an event"""
        pass
```

**File: `observers/console_observer.py`**

```python
class ConsoleObserver(BaseObserver):
    """Concrete Observer - prints to console"""
    
    def update(self, stage: str, event: str, data: Any = None):
        if event == 'subdomain_found':
            print(f"[+] Found subdomain: {data}")
        elif event == 'vulnerability_found':
            print(f"[!] Vulnerability: {data['type']}")
        elif event == 'error':
            print(f"[X] Error in {stage}: {data}")
```

**File: `observers/file_observer.py`**

```python
class FileObserver(BaseObserver):
    """Concrete Observer - writes to log file"""
    
    def update(self, stage: str, event: str, data: Any = None):
        log_entry = {
            'timestamp': datetime.now(),
            'stage': stage,
            'event': event,
            'data': data
        }
        self.log_file.write(json.dumps(log_entry) + '\n')
```

**File: `core/stage.py`**

```python
class Stage(ABC):
    """Subject - stages notify observers of events"""
    
    def __init__(self, name: str):
        self.name = name
        self.observers = []  # List of observers
    
    def attach_observer(self, observer: BaseObserver):
        """Attach an observer to this stage"""
        self.observers.append(observer)
    
    def notify(self, event: str, data: Any = None):
        """Notify all observers of an event"""
        for observer in self.observers:
            observer.update(self.name, event, data)
    
    @abstractmethod
    def execute(self, target: Target) -> bool:
        pass
```

**File: `stages/subdomain_enum.py`**

```python
class SubdomainEnumStage(Stage):
    """Subject - emits events during execution"""
    
    def execute(self, target: Target) -> bool:
        self.notify("start", f"Enumerating {target.domain}")
        
        for subdomain in self._enumerate():
            target.add_subdomain(subdomain)
            self.notify("subdomain_found", subdomain)  # Observers get notified
        
        self.notify("complete", f"Found {len(target.subdomains)} subdomains")
        return True
```

**File: `main.py`**

```python
# Setup observers
pipeline = Pipeline(data_store)
pipeline.attach(ConsoleObserver())
pipeline.attach(FileObserver('logs/scan.log'))
pipeline.attach(ProgressObserver())

# Run pipeline - all observers get notified automatically
pipeline.run("example.com")
```

### Benefits

✅ **Loose Coupling**: Stages don't know about logging/progress tracking  
✅ **Open/Closed**: Add new observers without modifying stages  
✅ **Single Responsibility**: Each observer handles one concern  
✅ **Dynamic Subscription**: Add/remove observers at runtime  
✅ **Testability**: Test stages without observers, or test observers independently

Direct implementation of [**Observer Pattern**](https://refactoring.guru/design-patterns/observer)

### Real-World Analogy

Think of YouTube subscriptions:
- **Subject**: A YouTuber uploads a video
- **Observers**: All subscribers get notified
- The YouTuber doesn't know who's subscribed or how they want notifications (email, push, SMS)
- Subscribers can unsubscribe without affecting the YouTuber

In GrayTera:
- **Subject**: A stage executes and finds something (subdomain, vulnerability)
- **Observers**: Console logger, file logger, progress tracker all get notified
- The stage doesn't know who's listening or what they do with the information
- You can add/remove observers without changing stage logic

---

## Pattern 4: Registry Pattern

### Intent
> Provide a centralized location for registering and retrieving objects of a specific type, enabling dynamic discovery and management.

### Problem We're Solving

We need to:
- Dynamically discover all available scanners/exploits
- Enable/disable scanners via configuration
- Add new scanners without modifying the scanning stage
- Support plugin-like architecture (future)

Without a registry, we'd have to hardcode:

```python
# BAD: Hardcoded scanner management
def get_scanners():
    return [
        SQLiScanner(),
        XSSScanner(),
        CSRFScanner(),
        # Have to modify this every time we add a scanner!
    ]
```

### Structure

```
┌────────────────────────────────────────────────────────────┐
│                     Registry Pattern                       │
└────────────────────────────────────────────────────────────┘

    ┌─────────────────────────┐
    │   ScannerRegistry       │
    ├─────────────────────────┤
    │ scanners: Dict[name,    │
    │              Scanner]   │
    ├─────────────────────────┤
    │ + register(scanner)     │
    │ + get_scanner(name)     │
    │ + get_all_scanners()    │
    │ + unregister(name)      │
    └───────────┬─────────────┘
                │ stores
                │
    ┌───────────▼─────────────┐
    │                         │
    │   {                     │
    │     "SQLi": SQLiScanner,│
    │     "XSS": XSSScanner,  │
    │     "CSRF": CSRFScanner │
    │   }                     │
    │                         │
    └─────────────────────────┘
```

### Implementation in GrayTera

**File: `scanners/scanner_registry.py`**

```python
class ScannerRegistry:
    """Central registry for all vulnerability scanners"""
    
    def __init__(self):
        self.scanners: Dict[str, BaseScanner] = {}
        self._register_default_scanners()
    
    def _register_default_scanners(self):
        """Auto-register built-in scanners"""
        self.register(SQLiScanner())
        # Add more as they're developed
        # self.register(XSSScanner())
        # self.register(CSRFScanner())
    
    def register(self, scanner: BaseScanner):
        """Register a new scanner"""
        self.scanners[scanner.name] = scanner
        print(f"[+] Registered scanner: {scanner.name}")
    
    def get_scanner(self, name: str) -> Optional[BaseScanner]:
        """Get a specific scanner by name"""
        return self.scanners.get(name)
    
    def get_all_scanners(self) -> List[BaseScanner]:
        """Get all registered scanners"""
        return list(self.scanners.values())
    
    def unregister(self, name: str):
        """Remove a scanner from registry"""
        if name in self.scanners:
            del self.scanners[name]
```

**File: `exploits/exploit_registry.py`**

```python
class ExploitRegistry:
    """Central registry for all exploits"""
    
    def __init__(self):
        self.exploits: Dict[str, BaseExploit] = {}
        self._register_default_exploits()
    
    def register(self, vuln_type: str, exploit: BaseExploit):
        """Register exploit for a vulnerability type"""
        self.exploits[vuln_type] = exploit
    
    def get_exploit(self, vuln_type: str) -> Optional[BaseExploit]:
        """Get exploit for a vulnerability type"""
        return self.exploits.get(vuln_type)
```

### Usage Example

```python
# Stage uses registry - doesn't need to know about specific scanners
class VulnerabilityScanStage(Stage):
    def __init__(self, config):
        self.scanner_registry = ScannerRegistry()
    
    def execute(self, target):
        # Automatically uses all registered scanners
        for scanner in self.scanner_registry.get_all_scanners():
            vulnerabilities = scanner.scan(target)
            # ...

# Adding a new scanner (future development)
class XXEScanner(BaseScanner):
    def __init__(self):
        super().__init__("XXE Scanner")
    
    def scan(self, url):
        # XXE detection logic
        pass

# Just register it - no need to modify VulnerabilityScanStage
registry = ScannerRegistry()
registry.register(XXEScanner())  # That's it!
```

### Benefits

✅ **Centralized Management**: Single source of truth for all scanners  
✅ **Dynamic Discovery**: Stages automatically find all registered scanners  
✅ **Plugin Architecture**: Easy to add/remove scanners at runtime  
✅ **Configuration**: Enable/disable scanners via config  
✅ **Testability**: Can mock the registry for testing

This is similar to the [**Service Locator**](https://martinfowler.com/articles/injection.html#UsingAServiceLocator) pattern or a simplified **Factory** pattern.

### Real-World Analogy

Think of a phone's app store:
- **Registry**: The app store catalog
- **Registration**: Developers publish apps to the store
- **Discovery**: Users browse all available apps
- **Installation**: Users choose which apps to use

In GrayTera:
- **Registry**: ScannerRegistry/ExploitRegistry
- **Registration**: Scanners register themselves
- **Discovery**: Scanning stage gets all available scanners
- **Execution**: Stage runs all registered scanners

---

## Pattern 5: Template Method Pattern

### Intent
> Define the skeleton of an algorithm in a base class, letting subclasses override specific steps without changing the algorithm's structure.

### Problem We're Solving

All stages share common behavior:
- Notify observers when starting
- Execute stage-specific logic
- Notify observers when completing
- Handle errors consistently

We want to avoid duplicating this structure in every stage.

### Structure

```
┌────────────────────────────────────────────────────────────┐
│                 Template Method Pattern                    │
└────────────────────────────────────────────────────────────┘

    ┌──────────────────────────┐
    │      <<abstract>>        │
    │         Stage            │
    ├──────────────────────────┤
    │ observers: []            │
    ├──────────────────────────┤
    │ + execute_template()     │  ◄── Template Method
    │ # execute(target)        │  ◄── Hook (abstract)
    │ + notify(event)          │
    └────────────┬─────────────┘
                 │ extends
    ┌────────────┼────────────┬───────────────┐
    │            │            │               │
┌───▼────┐  ┌───▼────┐  ┌───▼────┐     ┌────▼────┐
│Subdomain│ │  Vuln  │ │ Exploit│     │ Custom  │
│  Enum  │ │  Scan  │ │        │     │ Stage   │
│ Stage  │ │ Stage  │ │ Stage  │     │         │
└────────┘ └────────┘ └────────┘     └─────────┘
    │           │          │              │
    └───────────┴──────────┴──────────────┘
         Override execute(target)
```

### Implementation in GrayTera

**File: `core/stage.py`**

```python
class Stage(ABC):
    """Template for all pipeline stages"""
    
    def __init__(self, name: str):
        self.name = name
        self.observers = []
    
    def execute_template(self, target: Target) -> bool:
        """
        Template Method - defines the algorithm skeleton.
        This method is the same for all stages.
        """
        try:
            # Step 1: Notify start
            self.notify("start", f"Starting {self.name}")
            
            # Step 2: Execute stage-specific logic (hook method)
            success = self.execute(target)
            
            # Step 3: Notify completion
            if success:
                self.notify("complete", f"Completed {self.name}")
            else:
                self.notify("error", f"Failed {self.name}")
            
            return success
            
        except Exception as e:
            # Step 4: Handle errors consistently
            self.notify("error", f"Exception in {self.name}: {str(e)}")
            return False
    
    @abstractmethod
    def execute(self, target: Target) -> bool:
        """
        Hook Method - subclasses implement stage-specific logic.
        This is where stages differ from each other.
        """
        pass
    
    def notify(self, event: str, data: Any = None):
        """Helper method available to all stages"""
        for observer in self.observers:
            observer.update(self.name, event, data)
```

**File: `stages/subdomain_enum.py`**

```python
class SubdomainEnumStage(Stage):
    """Concrete implementation - only implements execute()"""
    
    def __init__(self, config: dict):
        super().__init__("Subdomain Enumeration")
        self.config = config
    
    def execute(self, target: Target) -> bool:
        """
        Stage-specific logic - the Template Method handles the rest.
        We don't need to worry about notifications or error handling.
        """
        try:
            subdomains = self._enumerate_subdomains(target.domain)
            
            for subdomain in subdomains:
                target.add_subdomain(subdomain)
                # We can still notify specific events
                self.notify("subdomain_found", subdomain)
            
            return True
            
        except Exception:
            return False
```

**File: `stages/vulnerability_scan.py`**

```python
class VulnerabilityScanStage(Stage):
    """Another concrete implementation"""
    
    def __init__(self, config: dict):
        super().__init__("Vulnerability Scanning")
        self.config = config
        self.scanner_registry = ScannerRegistry()
    
    def execute(self, target: Target) -> bool:
        """Stage-specific logic"""
        if not target.subdomains:
            self.notify("warning", "No subdomains to scan")
            return True
        
        self._scan_subdomains(target)
        return True
```

### Usage in Pipeline

```python
# Pipeline calls execute_template(), not execute()
for stage in self.stages:
    success = stage.execute_template(target)
    # Notifications, error handling already done by template method
    
    if not success:
        break
```

### Benefits

✅ **Code Reuse**: Common logic written once in base class  
✅ **Consistency**: All stages handle errors the same way  
✅ **Maintainability**: Changes to common behavior affect all stages  
✅ **Flexibility**: Stages can still customize behavior via hooks  
✅ **Enforcement**: Template method ensures stages follow the structure

Direct implementation of [**Template Method Pattern**](https://refactoring.guru/design-patterns/template-method)

### Real-World Analogy

Think of cooking recipes:
- **Template**: "1. Prepare ingredients, 2. Cook, 3. Serve, 4. Clean up"
- **Hook Method**: The "Cook" step differs for each recipe
- Making pasta vs. baking cake follows the same structure, but cooking differs

In GrayTera:
- **Template**: Start → Execute → Notify → Handle Errors
- **Hook Method**: The execute() step differs for each stage
- All stages follow the same structure, but their core logic differs

---

## Why These Patterns?

### Decision Matrix

We evaluated patterns based on:
- **Team Size**: 8 developers (need parallel work)
- **Skill Level**: Low to moderate (need simplicity)
- **Timeline**: 7 days (need quick implementation)
- **Future Growth**: Adding more vulnerability types
- **Testability**: Need isolated unit tests

| Pattern | Why Chosen | Alternatives Considered |
|---------|------------|------------------------|
| **Pipeline** | Natural fit for sequential pentesting workflow | State Machine (too complex), Simple loop (not extensible) |
| **Strategy** | Easy to add scanners in parallel by different devs | If-else chains (not extensible), Inheritance (too rigid) |
| **Observer** | Decouples logging from business logic | Callback functions (harder to manage), Direct calls (tight coupling) |
| **Registry** | Dynamic scanner discovery without hardcoding | Factory (too much boilerplate), Service Locator (same thing) |
| **Template Method** | Enforces consistent stage structure | Inheritance without template (code duplication), Composition (more complex) |

### Pattern Synergy

These patterns work together:

```
Pipeline
  ├── Contains Stages (Template Method)
  │     ├── Notifies Observers (Observer)
  │     └── Uses Scanners from Registry (Registry)
  │           └── Scanners use Strategy (Strategy)
  │
  └── Manages Data Store
```

### What We Avoided

❌ **Singleton** - Makes testing harder, hidden dependencies  
❌ **Factory** - Unnecessary abstraction for our use case  
❌ **Abstract Factory** - Over-engineering for 7-day timeline  
❌ **Builder** - Target object is simple enough  
❌ **Decorator** - Not needed for scanner enhancement  
❌ **Facade** - Stages are already simple interfaces  
❌ **Proxy** - No need for lazy loading or access control  

---

## Alternative Patterns Considered

### 1. Chain of Responsibility (Instead of Pipeline)

**Why NOT chosen:**

```python
# Chain of Responsibility approach
class Handler:
    def __init__(self):
        self.next_handler = None
    
    def set_next(self, handler):
        self.next_handler = handler
    
    def handle(self, request):
        # Process
        if self.next_handler:
            self.next_handler.handle(request)  # Pass to next

# Problem: Can skip stages, harder to track progress
```

**Issues:**
- ❌ Stages could skip processing
- ❌ Hard to implement pause/resume
- ❌ More complex for beginners
- ❌ Less intuitive for sequential workflow

**When to use:** When any handler can stop the chain (not our case)

---

### 2. State Machine (Instead of Pipeline)

**Why NOT chosen:**

```python
# State Machine approach
class PipelineState(Enum):
    ENUMERATING = 1
    SCANNING = 2
    EXPLOITING = 3
    DONE = 4

class Pipeline:
    def __init__(self):
        self.state = PipelineState.ENUMERATING
    
    def transition(self):
        if self.state == PipelineState.ENUMERATING:
            self.state = PipelineState.SCANNING
        # ... complex transition logic

# Problem: Over-engineered for linear workflow
```

**Issues:**
- ❌ More complex than needed
- ❌ Harder to understand for team
- ❌ More code to maintain
- ❌ Linear workflow doesn't need state transitions

**When to use:** When states have complex transition rules (not our case)

---

### 3. Command Pattern (Instead of Strategy)

**Why NOT chosen:**

```python
# Command Pattern approach
class ScanCommand:
    def __init__(self, scanner, target):
        self.scanner = scanner
        self.target = target
    
    def execute(self):
        return self.scanner.scan(self.target)
    
    def undo(self):
        # Undo scanning? Doesn't make sense

# Problem: Unnecessary complexity, no undo needed
```

**Issues:**
- ❌ We don't need undo/redo functionality
- ❌ Extra layer of abstraction
- ❌ More objects to manage
- ❌ Strategy is simpler for our use case

**When to use:** When you need undo/redo, queuing, or logging of operations

---

### 4. Mediator Pattern (Instead of Observer)

**Why NOT chosen:**

```python
# Mediator Pattern approach
class Mediator:
    def notify(self, sender, event):
        if event == "subdomain_found":
            self.console_logger.log(...)
            self.file_logger.log(...)
            self.progress_tracker.update(...)
        # Mediator knows about all components

# Problem: Mediator becomes a "god object"
```

**Issues:**
- ❌ Mediator knows about all observers (tight coupling)
- ❌ Hard to add new observers
- ❌ Centralized control point (bottleneck)
- ❌ Observer is more flexible

**When to use:** When components need complex interactions (not our case)

---

### 5. Visitor Pattern (For Scanners)

**Why NOT chosen:**

```python
# Visitor Pattern approach
class VulnerabilityVisitor:
    def visit_sqli(self, target):
        # SQLi detection logic
        pass
    
    def visit_xss(self, target):
        # XSS detection logic
        pass

# Problem: Awkward for adding new scanners
```

**Issues:**
- ❌ Adding new vulnerability types requires modifying visitor
- ❌ More complex than Strategy
- ❌ Violates Open/Closed principle in our context
- ❌ Doesn't fit our use case well

**When to use:** When you need to add new operations to existing classes (opposite of our need)

---

## Pattern Interactions

### How Patterns Work Together

```
┌─────────────────────────────────────────────────────────────┐
│                   Pattern Interaction Diagram                │
└─────────────────────────────────────────────────────────────┘

    main.py
       │
       ├─► Creates Pipeline ────────────────────┐
       │                                        │
       └─► Attaches Observers ─────────┐       │
                                       │       │
                                       ▼       ▼
                            ┌──────────────────────┐
                            │      Pipeline        │
                            │   (Pipeline Pattern) │
                            └──────────┬───────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                  │
                    ▼                  ▼                  ▼
          ┌─────────────────┐  ┌─────────────┐  ┌─────────────┐
          │ SubdomainEnum   │  │  VulnScan   │  │  Exploit    │
          │     Stage       │  │    Stage    │  │   Stage     │
          │ (Template)      │  │ (Template)  │  │ (Template)  │
          └────────┬────────┘  └──────┬──────┘  └──────┬──────┘
                   │                  │                 │
                   │                  │                 │
            notify()│           ┌─────▼─────┐    ┌─────▼─────┐
                   │           │  Registry  │    │  Registry │
                   │           │ (Registry) │    │ (Registry)│
                   │           └─────┬──────┘    └─────┬─────┘
                   │                 │                  │
                   │          ┌──────▼──────┐    ┌──────▼──────┐
                   │          │  Scanners   │    │  Exploits   │
                   │          │ (Strategy)  │    │ (Strategy)  │
                   │          └─────────────┘    └─────────────┘
                   │
                   ▼
          ┌─────────────────┐
          │    Observers    │
          │   (Observer)    │
          │  - Console      │
          │  - File         │
          │  - Progress     │
          └─────────────────┘
```

### Interaction Flow Example

**Scenario:** Running a scan and finding an SQLi vulnerability

```
1. main.py creates Pipeline
   └─► Pipeline Pattern: Initializes stages

2. main.py attaches ConsoleObserver, FileObserver
   └─► Observer Pattern: Stages can notify observers

3. Pipeline.run("example.com") called
   └─► Pipeline Pattern: Executes stages sequentially

4. Stage 1 (Subdomain Enum) starts
   └─► Template Method: execute_template() called
       ├─► Notifies "start" → Observers print to console/file
       ├─► Calls execute() (hook method)
       │   └─► Finds subdomain "api.example.com"
       │       └─► Notifies "subdomain_found" → Observers log it
       └─► Notifies "complete" → Observers print completion

5. Stage 2 (Vuln Scan) starts
   └─► Template Method: execute_template() called
       ├─► Notifies "start" → Observers print
       ├─► Gets scanners from Registry
       │   └─► Registry Pattern: Returns [SQLiScanner, XSSScanner, ...]
       ├─► For each subdomain:
       │   └─► For each scanner:
       │       └─► Strategy Pattern: scanner.scan(subdomain)
       │           └─► SQLiScanner finds vulnerability
       │               └─► Notifies "vulnerability_found" → Observers log
       └─► Notifies "complete" → Observers print

6. Stage 3 (Exploit) starts
   └─► Template Method: execute_template() called
       ├─► Gets exploit from Registry
       │   └─► Registry Pattern: Returns SQLiExploit
       ├─► Strategy Pattern: exploit.execute(vulnerability)
       │   └─► Notifies "exploit_success" → Observers log
       └─► Notifies "complete" → Observers print

7. Pipeline saves results to DataStore
   └─► Persistence: JSON + pickle files
```

### Data Flow Through Patterns

```
Target Object Flow:
                                         
main.py                                  
  │                                      
  ├─► Creates Target("example.com")     
  │                                      
  └─► Pipeline.run(target) ────────────► Pipeline Pattern
                                             │
                  ┌──────────────────────────┘
                  │
    ┌─────────────┼─────────────┬────────────────┐
    │             │             │                │
    ▼             ▼             ▼                ▼
Stage 1       Stage 2       Stage 3         DataStore
(Subdomain)   (VulnScan)    (Exploit)       (Saves)
    │             │             │                │
    │             │             │                │
Enriches      Enriches      Enriches         Persists
Target        Target        Target           Target
    │             │             │                │
    └─────────────┴─────────────┴────────────────┘
                      │
                      ▼
              Target {
                domain: "example.com"
                subdomains: ["api.example.com", ...]
                vulnerabilities: [SQLi at /login.php]
                exploited: [DB version: MySQL 5.7]
              }
```

---

## Benefits of This Architecture

### 1. Modularity
Each pattern handles a specific concern:
- **Pipeline**: Workflow orchestration
- **Strategy**: Vulnerability-specific algorithms
- **Observer**: Cross-cutting concerns (logging, monitoring)
- **Registry**: Component discovery
- **Template Method**: Common structure enforcement

### 2. Extensibility
Adding new features is straightforward:

**Adding a new vulnerability scanner:**
```python
# 1. Create scanner (Strategy Pattern)
class XXEScanner(BaseScanner):
    def scan(self, url): ...

# 2. Register it (Registry Pattern)
registry.register(XXEScanner())

# That's it! VulnerabilityScanStage automatically uses it
```

**Adding a new observer:**
```python
# 1. Create observer (Observer Pattern)
class ReportObserver(BaseObserver):
    def update(self, stage, event, data): ...

# 2. Attach it
pipeline.attach(ReportObserver())

# That's it! All stages notify it automatically
```

### 3. Team Collaboration
Clear boundaries for parallel development:

| Team | Component | Pattern Used |
|------|-----------|--------------|
| Team 1 | Pipeline + CLI | Pipeline Pattern |
| Team 2 | Subdomain Enum | Template Method |
| Team 3 | SQLi Scanner | Strategy Pattern |
| Team 4 | SQLi Exploit | Strategy Pattern |
| Team 5 | Observers | Observer Pattern |

Teams can work independently without stepping on each other's toes.

### 4. Testability
Each pattern enables isolated testing:

```python
# Test a scanner in isolation (Strategy)
def test_sqli_scanner():
    scanner = SQLiScanner()
    vulns = scanner.scan("http://testsite.com")
    assert len(vulns) > 0

# Test a stage without observers (Template Method)
def test_subdomain_enum():
    stage = SubdomainEnumStage(config)
    target = Target("example.com")
    success = stage.execute(target)
    assert success
    assert len(target.subdomains) > 0

# Test pipeline with mock stages (Pipeline)
def test_pipeline():
    mock_stage = MockStage()
    pipeline = Pipeline(data_store)
    pipeline.stages = [mock_stage]
    pipeline.run("example.com")
    assert mock_stage.executed

# Test observer in isolation (Observer)
def test_console_observer():
    observer = ConsoleObserver()
    observer.update("TestStage", "info", "Test message")
    # Assert console output
```

### 5. Maintainability
Changes are localized:

| Change Required | Files Affected | Patterns Involved |
|-----------------|----------------|-------------------|
| Add new scanner | `scanners/new_scanner.py`, `scanner_registry.py` | Strategy, Registry |
| Change logging format | `observers/console_observer.py` | Observer |
| Modify stage order | `core/pipeline.py` | Pipeline |
| Add stage validation | `core/stage.py` | Template Method |
| Change persistence | `core/data_store.py` | None (isolated) |

---

## Real-World Comparison

### GrayTera Architecture vs. Industry Tools

| Tool | Architecture | Similarities | Differences |
|------|--------------|--------------|-------------|
| **Metasploit** | Module-based | Strategy for exploits, Registry for modules | More complex plugin system |
| **Burp Suite** | Extension-based | Observer for logging, Strategy for scanners | Java-based, more abstraction layers |
| **OWASP ZAP** | Plugin architecture | Similar stage-based scanning | XML-based plugin registration |
| **Nuclei** | Template-based | Strategy for templates | YAML-driven, not OOP |
| **SQLMap** | Monolithic | Similar strategy for techniques | Less modular, harder to extend |

**GrayTera's Approach:**
- ✅ Simpler than Metasploit (easier for students)
- ✅ More structured than SQLMap (better for teams)
- ✅ Python-native (no XML/YAML complexity)
- ✅ Educational focus (clear patterns)

---

## Learning Resources

### Recommended Reading Order

1. **Start Here:**
   - [Refactoring.Guru - Design Patterns](https://refactoring.guru/design-patterns)
   - Focus on: Strategy, Observer, Template Method

2. **Dive Deeper:**
   - "Design Patterns: Elements of Reusable Object-Oriented Software" (Gang of Four)
   - "Head First Design Patterns" (easier to read)

3. **Python-Specific:**
   - "Python Design Patterns" by Brandon Rhodes
   - [Python Patterns Guide](https://python-patterns.guide/)

### Pattern Examples from GrayTera

For each pattern in this document, you can:
1. Read the explanation
2. Look at the code in the codebase
3. Run tests to see it in action
4. Try adding a new scanner/observer to practice

### Exercises for Team

**Exercise 1: Add a new scanner**
- Create `scanners/xss_scanner.py`
- Implement `BaseScanner` interface
- Register in `ScannerRegistry`
- Run the tool and verify it works

**Exercise 2: Add a new observer**
- Create `observers/email_observer.py`
- Implement `BaseObserver` interface
- Attach to pipeline
- Verify it receives notifications

**Exercise 3: Add a new stage**
- Create `stages/reporting.py`
- Inherit from `Stage`
- Implement `execute()` method
- Add to pipeline stages

---

## Glossary

**Base Class / Abstract Class**: A class that defines an interface but cannot be instantiated directly. Subclasses must implement abstract methods.

**Concrete Class**: A class that implements all abstract methods from its base class and can be instantiated.

**Hook Method**: A method in a base class that subclasses can override to customize behavior.

**Template Method**: A method in a base class that defines the skeleton of an algorithm, calling hook methods.

**Strategy**: An interchangeable algorithm encapsulated in its own class.

**Observer**: An object that watches another object and gets notified of changes.

**Registry**: A centralized location for storing and retrieving objects.

**Subject**: An object that notifies observers when its state changes.

**Pipeline**: A series of stages where each stage processes data and passes it to the next.

**Decoupling**: Reducing dependencies between components so they can change independently.

**Open/Closed Principle**: Software entities should be open for extension but closed for modification.

---

## Conclusion

GrayTera's architecture demonstrates how well-chosen design patterns can:

✅ **Simplify complexity** - Clear structure for pentesting workflow  
✅ **Enable teamwork** - 8 developers working in parallel  
✅ **Support growth** - Easy to add new scanners/exploits  
✅ **Ensure quality** - Testable, maintainable code  
✅ **Meet deadlines** - 7-day implementation possible  

The combination of **Pipeline + Strategy + Observer + Registry + Template Method** creates a flexible, extensible architecture that's:
- Simple enough for students to understand
- Professional enough for real-world use
- Modular enough for team development
- Extensible enough for future growth

### Key Takeaways

1. **Not all patterns are needed** - We chose 5 patterns that solve specific problems
2. **Patterns work together** - They complement each other when used correctly
3. **Simplicity matters** - We avoided over-engineering for 7-day timeline
4. **Team structure drives architecture** - 8 developers need clear boundaries
5. **Learn by doing** - Implement patterns to truly understand them

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Nov 2025 | Initial documentation |

## Contributors

- Team 1: Pipeline & Core Architecture
- Team 2: Subdomain Enumeration
- Team 3: SQLi Scanner
- Team 4: SQLi Exploit
- All Teams: Design Pattern Implementation

---

## Appendix: Quick Pattern Reference

### When to Use Each Pattern

| Pattern | Use When | Don't Use When |
|---------|----------|----------------|
| **Pipeline** | Sequential processing needed | Order doesn't matter |
| **Strategy** | Multiple algorithms for same task | Only one algorithm |
| **Observer** | Many objects need notifications | Only one listener |
| **Registry** | Dynamic component discovery | Fixed set of components |
| **Template Method** | Common structure, varying steps | No common structure |

### Pattern Cheat Sheet

```python
# Pipeline Pattern
class Pipeline:
    def run(self, data):
        for stage in self.stages:
            data = stage.process(data)
        return data

# Strategy Pattern
class Context:
    def __init__(self, strategy):
        self.strategy = strategy
    
    def execute(self):
        return self.strategy.do_algorithm()

# Observer Pattern
class Subject:
    def attach(self, observer):
        self.observers.append(observer)
    
    def notify(self, event):
        for obs in self.observers:
            obs.update(event)

# Registry Pattern
class Registry:
    def register(self, name, obj):
        self.items[name] = obj
    
    def get(self, name):
        return self.items[name]

# Template Method Pattern
class Base:
    def template_method(self):
        self.step1()
        self.step2()  # Hook - subclasses override
        self.step3()
    
    @abstractmethod
    def step2(self):
        pass
```

---

**End of Document**

For questions or clarifications, refer to:
- Code comments in the codebase
- [Refactoring.Guru](https://refactoring.guru/design-patterns)
- Team leads for each component