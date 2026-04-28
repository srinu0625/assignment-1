using UnityEngine;
using System.Collections.Generic;

public class PlayerController : MonoBehaviour
{
    [Header("Movement")]
    public float walkSpeed = 5f;
    public float runSpeed = 10f;
    public float jumpForce = 8f;
    public float mouseSensitivity = 2f;
    
    [Header("Camera")]
    public Camera playerCamera;
    public float cameraDistance = 5f;
    public float cameraHeight = 2f;
    
    [Header("Combat")]
    public LayerMask shootableLayers;
    public GameObject bulletImpactPrefab;
    public AudioClip shootSound;
    
    [Header("Weapons")]
    public List<Weapon> weapons = new List<Weapon>();
    
    [System.NonSerialized] public float health = 100f;
    [System.NonSerialized] public string currentWeapon = "Fist";
    [System.NonSerialized] public bool inVehicle = false;
    
    private CharacterController controller;
    private Vehicle currentVehicle;
    private float verticalVelocity;
    private int currentWeaponIndex = 0;
    private float lastShootTime;
    private AudioSource audioSource;
    
    [System.Serializable]
    public class Weapon
    {
        public string name;
        public int damage;
        public float fireRate;
        public int ammo;
        public float range;
        public bool automatic;
        public GameObject weaponModel;
    }
    
    void Start()
    {
        controller = GetComponent<CharacterController>();
        audioSource = GetComponent<AudioSource>();
        
        // Create default weapons
        weapons.Add(new Weapon { name = "Pistol", damage = 25, fireRate = 2f, ammo = 12, range = 50f, automatic = false });
        weapons.Add(new Weapon { name = "Rifle", damage = 35, fireRate = 8f, ammo = 30, range = 100f, automatic = true });
        
        Cursor.lockState = CursorLockMode.Locked;
    }
    
    void Update()
    {
        if (inVehicle)
        {
            HandleVehicleInput();
        }
        else
        {
            HandleMovement();
            HandleCombat();
            HandleWeaponSwitch();
            CheckVehicleEntry();
        }
        
        UpdateCamera();
    }
    
    void HandleMovement()
    {
        // Ground check
        bool isGrounded = controller.isGrounded;
        
        if (isGrounded && verticalVelocity < 0)
            verticalVelocity = -0.5f;
        
        // Input
        float horizontal = Input.GetAxis("Horizontal");
        float vertical = Input.GetAxis("Vertical");
        
        float speed = Input.GetKey(KeyCode.LeftShift) ? runSpeed : walkSpeed;
        
        // Calculate movement direction relative to camera
        Transform camTransform = playerCamera.transform;
        Vector3 forward = camTransform.forward;
        Vector3 right = camTransform.right;
        forward.y = 0;
        right.y = 0;
        forward.Normalize();
        right.Normalize();
        
        Vector3 moveDirection = (forward * vertical + right * horizontal).normalized;
        
        // Apply movement
        controller.Move(moveDirection * speed * Time.deltaTime);
        
        // Rotation
        if (moveDirection != Vector3.zero)
        {
            Quaternion lookRotation = Quaternion.LookRotation(moveDirection);
            transform.rotation = Quaternion.Slerp(transform.rotation, lookRotation, Time.deltaTime * 10f);
        }
        
        // Jump
        if (Input.GetButtonDown("Jump") && isGrounded)
        {
            verticalVelocity = jumpForce;
        }
        
        // Gravity
        verticalVelocity += Physics.gravity.y * Time.deltaTime;
        controller.Move(new Vector3(0, verticalVelocity, 0) * Time.deltaTime);
    }
    
    void HandleCombat()
    {
        if (currentWeaponIndex == -1) return; // Fists
        
        Weapon weapon = weapons[currentWeaponIndex];
        
        bool shouldShoot = weapon.automatic ? Input.GetMouseButton(0) : Input.GetMouseButtonDown(0);
        
        if (shouldShoot && Time.time > lastShootTime + (1f/weapon.fireRate) && weapon.ammo > 0)
        {
            Shoot(weapon);
        }
        
        // Reload
        if (Input.GetKeyDown(KeyCode.R))
        {
            weapon.ammo = weapon.name == "Pistol" ? 12 : 30;
        }
    }
    
    void Shoot(Weapon weapon)
    {
        lastShootTime = Time.time;
        weapon.ammo--;
        
        // Raycast shooting
        RaycastHit hit;
        Vector3 shootDirection = playerCamera.transform.forward;
        
        // Add recoil/randomness
        shootDirection += new Vector3(Random.Range(-0.05f, 0.05f), Random.Range(-0.05f, 0.05f), 0);
        
        if (Physics.Raycast(playerCamera.transform.position, shootDirection, out hit, weapon.range, shootableLayers))
        {
            // Damage enemy
            EnemyAI enemy = hit.collider.GetComponent<EnemyAI>();
            if (enemy != null)
            {
                enemy.TakeDamage(weapon.damage);
                GTAGameManager.Instance.AddWantedLevel(1);
            }
            
            // Impact effect
            if (bulletImpactPrefab != null)
                Instantiate(bulletImpactPrefab, hit.point, Quaternion.LookRotation(hit.normal));
        }
        
        // Sound
        if (audioSource && shootSound)
            audioSource.PlayOneShot(shootSound);
    }
    
    void HandleWeaponSwitch()
    {
        if (Input.GetKeyDown(KeyCode.Alpha1)) currentWeaponIndex = -1; // Fists
        if (Input.GetKeyDown(KeyCode.Alpha2) && weapons.Count > 0) currentWeaponIndex = 0;
        if (Input.GetKeyDown(KeyCode.Alpha3) && weapons.Count > 1) currentWeaponIndex = 1;
        
        if (currentWeaponIndex == -1)
            currentWeapon = "Fist";
        else if (currentWeaponIndex < weapons.Count)
            currentWeapon = weapons[currentWeaponIndex].name;
    }
    
    void CheckVehicleEntry()
    {
        if (Input.GetKeyDown(KeyCode.F))
        {
            // Check for nearby vehicles
            Collider[] nearby = Physics.OverlapSphere(transform.position, 3f);
            foreach (Collider col in nearby)
            {
                Vehicle vehicle = col.GetComponent<Vehicle>();
                if (vehicle != null && !vehicle.occupied)
                {
                    EnterVehicle(vehicle);
                    break;
                }
            }
        }
    }
    
    void EnterVehicle(Vehicle vehicle)
    {
        inVehicle = true;
        currentVehicle = vehicle;
        vehicle.occupied = true;
        vehicle.driver = this;
        
        controller.enabled = false;
        transform.SetParent(vehicle.transform);
        transform.localPosition = Vector3.zero;
        transform.localRotation = Quaternion.identity;
        
        // Disable rendering of player mesh if you have one
        // GetComponent<MeshRenderer>().enabled = false;
    }
    
    void HandleVehicleInput()
    {
        if (Input.GetKeyDown(KeyCode.F))
        {
            ExitVehicle();
            return;
        }
        
        // Vehicle controls are handled by Vehicle.cs, we just pass input
        float horizontal = Input.GetAxis("Horizontal");
        float vertical = Input.GetAxis("Vertical");
        bool handbrake = Input.GetKey(KeyCode.Space);
        
        if (currentVehicle != null)
            currentVehicle.ProcessInput(horizontal, vertical, handbrake);
    }
    
    void ExitVehicle()
    {
        inVehicle = false;
        if (currentVehicle != null)
        {
            currentVehicle.occupied = false;
            currentVehicle.driver = null;
            
            // Eject player
            transform.SetParent(null);
            transform.position = currentVehicle.transform.position + currentVehicle.transform.right * 2f;
            transform.rotation = Quaternion.identity;
        }
        
        controller.enabled = true;
        currentVehicle = null;
    }
    
    void UpdateCamera()
    {
        if (inVehicle && currentVehicle != null)
        {
            // Chase cam for vehicle
            Vector3 targetPos = currentVehicle.transform.position - currentVehicle.transform.forward * 10f + Vector3.up * 5f;
            playerCamera.transform.position = Vector3.Lerp(playerCamera.transform.position, targetPos, Time.deltaTime * 5f);
            playerCamera.transform.LookAt(currentVehicle.transform.position + Vector3.up * 2f);
        }
        else
        {
            // Third person follow cam
            Vector3 targetPos = transform.position - transform.forward * cameraDistance + Vector3.up * cameraHeight;
            playerCamera.transform.position = Vector3.Lerp(playerCamera.transform.position, targetPos, Time.deltaTime * 10f);
            playerCamera.transform.LookAt(transform.position + Vector3.up * 1.5f);
            
            // Mouse look
            float mouseX = Input.GetAxis("Mouse X") * mouseSensitivity;
            float mouseY = Input.GetAxis("Mouse Y") * mouseSensitivity;
            
            transform.Rotate(Vector3.up * mouseX);
        }
    }
    
    public void TakeDamage(float damage)
    {
        health -= damage;
        if (health <= 0)
        {
            Respawn();
        }
    }
    
    void Respawn()
    {
        health = 100;
        transform.position = Vector3.zero;
        GTAGameManager.Instance.ReduceWantedLevel(999); // Clear wanted
    }
    
    void OnTriggerEnter(Collider other)
    {
        // Pickup weapons/health
        if (other.CompareTag("WeaponPickup"))
        {
            // Add ammo or new weapon
            Destroy(other.gameObject);
        }
    }
}
